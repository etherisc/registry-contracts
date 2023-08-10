from brownie.network import accounts
from brownie.network.account import Account

from brownie import (
    interface,
    history,
    network,
    web3,
    DIP,
    USD1,
    USD2,
    MockInstance,
    MockInstanceRegistry,
    OwnableProxyAdmin,
    ChainNft,
    ChainRegistryV01,
    StakingV03,
)

from scripts.util import (
    contract_from_address,
    get_package,
    unix_timestamp,
    wait_for_confirmations,
)

from scripts.const import (
    DIP_MAINNET_ADDRESS,
    USDT_MAINNET_ADDRESS,
    ACCOUNTS_MNEMONIC,
    INSTANCE_OPERATOR,
    REGISTRY_OWNER,
    STAKING_OWNER,
    PROXY_ADMIN_OWNER,
    STAKER1,
    STAKER2,
    OUTSIDER,
    GIF_ACTOR,
    ZERO_ADDRESS,
)

GAS_PRICE_SAFETY_FACTOR = 1.25

GAS_0 = 0
GAS_S = 1 * 10**6
GAS_SM = 3 * 10**6
GAS_M = 6 * 10**6
GAS_L = 10 * 10**6

GAS_REGISTRY = {
    INSTANCE_OPERATOR: GAS_SM, # dip,usdt token for testnets
    PROXY_ADMIN_OWNER: GAS_M, # proxy adins for registry, staking
    REGISTRY_OWNER: GAS_L, # registry contract, some wiring
    STAKING_OWNER: GAS_M, # staking contract some wiring
    STAKER1: GAS_S
}

GAS_MOCK = {
    INSTANCE_OPERATOR: GAS_0, # included in registry seteup
    PROXY_ADMIN_OWNER: GAS_0, # included in registry seteup
    REGISTRY_OWNER: GAS_0, # included in registry seteup
    STAKING_OWNER: GAS_0, # included in registry seteup
    STAKER1: GAS_0, # included in registry seteup
}

PROXY_ADMIN_CONTRACT = OwnableProxyAdmin
NFT_CONTRACT = ChainNft
REGISTRY_CONTRACT = ChainRegistryV01
STAKING_CONTRACT = StakingV03

MOCK_INSTANCE_CONTRACT = MockInstance
MOCK_REGISTRY_CONTRACT = MockInstanceRegistry

MOCK_RISKPOOL_ID = 3
MOCK_BUNDLE_ID = 8

NFT_USDT = 'usdt'
NFT_INSTANCE = 'instance'
NFT_RISKPOOL = 'riskpool'
NFT_BUNDLE = 'bundle'
NFT_STAKE = 'stake'


# see gif-interface IComponent.ComponentState
STATE_COMPONENT = {
    0: 'Created',
    1: 'Proposed',
    2: 'Declined',
    3: 'Active',
    4: 'Paused',
    5: 'Suspended',
    6: 'Archived'
}

# see gif-interface IBundle.BundleState
STATE_BUNDLE = {
    0: 'Active',
    1: 'Locked',
    2: 'Closed',
    3: 'Burned'
}

# load openzeppelin contracts
oz = get_package('OpenZeppelin')

def help():
    print('from scripts.util import contract_from_address, new_accounts, get_package')
    print('from scripts.deploy_registry import all_in_1, get_accounts, get_stakeholder_accounts, check_funds, amend_funds, verify_deploy, help')
    print('a = get_accounts() # opt param mnemonic=None')
    print('(a, mnemonic) = new_accounts() # opt param count=20')
    print('stakeholder_accounts = get_stakeholder_accounts(a)')
    print('check_funds(stakeholder_accounts)')
    print('# amend_funds(stakeholder_accounts)')
    print()
    print('(registry, staking, nft, nft_ids, dip, usdt, instance_service, instance_operator, registry_owner, staking_owner, proxy_admin) = all_in_1(stakeholder_accounts)')
    print('instance_service.getBundle({}).dict()'.format(MOCK_BUNDLE_ID))
    print("registry.getNftInfo(nft_ids['stake']).dict()")
    print("registry.decodeStakeData(nft_ids['stake']).dict()")
    print("staking.getInfo(nft_ids['stake']).dict()")


def link_to_product(
    staking_address, 
    product_address, 
    staking_owner,
    registry_owner,
    riskpool_keeper,
    instance_name = None,
    reward_rate = 0.125,
    staking_rate = 0.100,
    bundle_lifetime = 14 * 24 * 3600
):

    print('1) obtaining staking and registry contracts')
    staking = contract_from_address(StakingV03, staking_address)
    registry = contract_from_address(ChainRegistryV01, staking.getRegistry())

    print('2) obtaining product and token contracts')
    product = contract_from_address(interface.IProductFacade, product_address)
    token = contract_from_address(interface.IERC20Metadata, product.getToken())

    print('3) obtaining instance service')
    registry_address = product.getRegistry()

    (
        is_contract,
        contract_size,
        chain_id,
        instance_id,
        is_valid,
        instance_service_address
    ) = registry.probeInstance(registry_address)

    if not is_valid:
        print('ERROR: registry address {} leads to invalid instance'.format(registry_address))

        return (
            registry,
            staking,
            product,
            None
        )
    
    print('4) obtaining riskpool contract')
    instance_service = contract_from_address(interface.IInstanceServiceFacade, instance_service_address)
    (riskpool, riskpool_id) = get_riskpool(instance_service, product)
    instance_id = instance_service.getInstanceId()

    fro = {'from': registry_owner}
    fso = {'from': staking_owner}
    frk = {'from': riskpool_keeper}

    print('5) token {} registration'.format(token.symbol()))
    try:
        nft_id = registry.getTokenNftId(chain_id, token)
        print('   token already registered (nftId: {})'.format(nft_id))
    except Exception as e:
        tx = registry.registerToken(chain_id, token, '', fro)
        print_registry_tx_info(tx)

    print("6) instance '{}' registration (instance id: {})".format(instance_name, instance_id))
    try:
        nft_id = registry.getInstanceNftId(instance_id)
        print('   instance already registered (nftId: {})'.format(nft_id))
    except Exception as e:
        tx = registry.registerInstance(registry_address, instance_name, '', fro)
        wait_for_confirmations(tx)
        print_registry_tx_info(tx)

    print('7) riskpool {} registration'.format(riskpool_id))
    try:
        nft_id = registry.getComponentNftId(instance_id, riskpool_id)
        print('   token already registered (nftId: {})'.format(nft_id))
    except Exception as e:
        tx = registry.registerComponent(instance_id, riskpool_id, '', fro)
        wait_for_confirmations(tx)
        print_registry_tx_info(tx)

    active_bundles = riskpool.activeBundles()
    if active_bundles > 0:
        print('8) bundle registration ({} bundles)'.format(active_bundles))

        for i in range(active_bundles):
            bundle_id = riskpool.getActiveBundleId(i)

            try:
                nft_id = registry.getBundleNftId(instance_id, bundle_id)
                print('   bundle {} already registered (bundleId: {}, nftId: {})'
                    .format(i+1, bundle_id, nft_id))
            except Exception as e:
                bundle_name = 'bundle-{}'.format(i)
                bundle_expiry_at = unix_timestamp() + bundle_lifetime
                print('   register bundle {} (bundleId: {}, lifetime: {})'
                    .format(i+1, bundle_id, bundle_lifetime))
                tx = registry.registerBundle(
                    instance_id,
                    riskpool_id,
                    bundle_id,
                    bundle_name,
                    bundle_expiry_at,
                    fro)
                print_registry_tx_info(tx)

    print('9) checking reward rate (target: {:.3f})'.format(reward_rate))
    current_rate = staking.rewardRate()
    target_rate = staking.toRate(int(1000 * reward_rate), -3)
    if current_rate == target_rate:
        print('   reward rate already adjusting ')
    else:
        print('   adjusting reward rate from {:.3f} to target'.format(current_rate/10**staking.rateDecimals()))
        staking.setRewardRate(target_rate, fso)

    print('10) checking dip/usdt staking rate (target: {:.3f})'.format(staking_rate))
    current_rate = staking.stakingRate(chain_id, token)
    target_rate = staking.toRate(int(1000 * staking_rate), -3)
    if current_rate == target_rate:
        print('   staking rate already adjusting ')
    else:
        print('   adjusting staking rate from {:.3f} to target'.format(current_rate/10**staking.rateDecimals()))
        staking.setStakingRate(chain_id, token, target_rate, fso)

    print('11) link riskpool {} with staking {})'.format(riskpool_id, staking))
    if riskpool.getStaking() == staking:
        print('   riskpool and staking already linked')
    else:
        riskpool.setStakingAddress(staking, frk)

    print('linking process completed')

    return (
        registry,
        staking,
        product,
        instance_service
    )


def print_registry_tx_info(tx):
    if 'LogChainRegistryObjectRegistered' in tx.events:
        evt = dict(history[-1].events['LogChainRegistryObjectRegistered'])
        print('nft minted (id: {}, type: {})'.format(evt['id'], evt['objectType']))

        return evt['id']
    
    return 0


def get_riskpool(instance_service, product):
    riskpool_id = product.getRiskpoolId()
    riskpool_address = instance_service.getComponent(riskpool_id)
    riskpool = contract_from_address(interface.IRiskpoolFacade, riskpool_address)

    return (riskpool, riskpool_id)


def get_stakeholder_accounts(accts):
    if len(accts) >= 10:
        return {
            INSTANCE_OPERATOR: accts[GIF_ACTOR[INSTANCE_OPERATOR]],
            PROXY_ADMIN_OWNER: accts[GIF_ACTOR[PROXY_ADMIN_OWNER]],
            REGISTRY_OWNER: accts[GIF_ACTOR[REGISTRY_OWNER]],
            STAKING_OWNER: accts[GIF_ACTOR[STAKING_OWNER]],
            STAKER1: accts[GIF_ACTOR[STAKER1]],
        }


def get_accounts(mnemonic=None):
    if not mnemonic and len(accounts) >= 20:
        return accounts
    
    if mnemonic:
        return accounts.from_mnemonic(mnemonic, count=20)
    
    print('ERROR: mnemonic is mandatory on chains without prefilled accounts (len => 20)')
    return None


def get_gas_price():
    return web3.eth.gas_price


def _print_constants(gas_price, safety_factor, gp):
    print('chain id: {}'.format(web3.eth.chain_id))
    print('gas price [GWei]: {}'.format(gas_price/10**9))
    print('safe gas price [GWei]: {}'.format(gp/10**9))
    print('gas price safety factor: {}'.format(safety_factor))


def amend_funds(
    stakeholder_accounts,
    gas_price=None,
    safety_factor=GAS_PRICE_SAFETY_FACTOR,
    include_mock_setup=True
):
    if web3.chain_id == 1:
        print('amend_funds not available on mainnet')
        return

    # check stakeholder accounts
    a = stakeholder_accounts
    assert INSTANCE_OPERATOR in a
    assert PROXY_ADMIN_OWNER in a
    assert REGISTRY_OWNER in a
    assert STAKING_OWNER in a
    assert STAKER1 in a

    if not gas_price:
        gas_price = get_gas_price()

    gp = int(safety_factor * gas_price)

    g = GAS_REGISTRY
    if include_mock_setup:
        g = get_balance_sum(GAS_REGISTRY, GAS_MOCK)
    
    for s in a.keys():
        bs = a[s].balance()
        if bs >= gp * g[s]:
            print('{}.balance(): {} OK'.format(s, bs))
        else:
            ms = gp * g[s] - bs
            print('{}.balance(): {} transfer {} from instanceOperator'.format(s, bs, ms))
            a['instanceOperator'].transfer(a[s], ms)


def check_funds(
    stakeholder_accounts,
    gas_price=None,
    safety_factor=GAS_PRICE_SAFETY_FACTOR,
    include_mock_setup=True,
    print_requirements=False
):
    # check stakeholder accounts
    a = stakeholder_accounts
    assert INSTANCE_OPERATOR in a
    assert PROXY_ADMIN_OWNER in a
    assert REGISTRY_OWNER in a
    assert STAKING_OWNER in a
    assert STAKER1 in a

    if not gas_price:
        gas_price = get_gas_price()

    gp = int(safety_factor * gas_price)

    g = GAS_REGISTRY
    if include_mock_setup:
        g = get_balance_sum(GAS_REGISTRY, GAS_MOCK)

    _print_constants(gas_price, safety_factor, gp)

    if print_requirements:
        print('--- funding requirements ---')
        print('Name;Address;ETH')

        for accountName, requiredAmount in g.items():
            print('{};{};{:.4f}'.format(
                accountName,
                a[accountName],
                gp * requiredAmount / 10**18
            ))

        print('--- end of funding requirements ---')

    funds_available = 0
    checked_accounts = 0
    g_missing = 0

    for s in g.keys():
        bs = a[s].balance()
        funds_available += bs
        checked_accounts += 1

        if bs >= gp * g[s]:
            print('{} funding OK, has [ETH]{:.5f} ([wei]{})'.format(s, bs/10**18, bs))
        else:
            ms = gp * g[s] - bs
            print('{} needs [ETH]{:.5f}, has [ETH]{:.5f} ([wei]{})'.format(s, ms/10**18, bs/10**18, bs))
            g_missing += ms

    if g_missing > 0:
        if a[INSTANCE_OPERATOR].balance() >= gp * g[INSTANCE_OPERATOR] + g_missing:
            print('{} balance sufficient to fund other accounts, use amend_funds(a) and try again'.format(INSTANCE_OPERATOR))
        else:
            # add max tx gas to distribute funds (1x eth transfer tx=21k gas)
            g_missing += (len(g.keys()) - 1) * 21000
            print('{} needs additional funding of [ETH]{:.6f} ([wei]{}) to fund other accounts'
                .format(INSTANCE_OPERATOR, g_missing/10**18, g_missing))

    print('total funds available ({} accounts) [ETH] {:.6f}, [wei] {}'
        .format(checked_accounts, funds_available/10**18, funds_available))

    assert g_missing == 0, "ERROR missing funds/wrong fund distribution detected"


def all_in_1(
    stakeholder_accounts,
    dip_address=None,
    usdt_address=None,
    include_mock_setup=True,
    nft_address=None,
    registry_proxy_admin_address=None,
    staking_proxy_admin_address=None,
    publish=False
):
    if not stakeholder_accounts:
        if web3.chain_id == 1337:
            stakeholder_accounts = accounts_ganache()
        else:
            print('stakeholder_accounts must not be None')
            assert stakeholder_accounts

    # check stakeholder accounts
    a = stakeholder_accounts
    balances_before = get_balances(a)
    gas_price = get_gas_price()
    check_funds(a, gas_price, include_mock_setup)

    dip = connect_to_dip(a, dip_address, publish)
    usdt = connect_to_usdt(a, usdt_address, publish)

    (
        proxy_admin, 
        registry_owner,
        registry,
        nft
    ) = deploy_registry(
        a,
        nft_address=nft_address,
        proxy_admin_address=registry_proxy_admin_address,
        publish=publish)

    (
        proxy_admin, 
        staking_owner,
        staking
    ) = deploy_staking(
        a,
        proxy_admin_address=staking_proxy_admin_address,
        publish=publish)

    print('>>> set staking contract in registry')
    # needed for onlyStaking modifier
    # context only staking is allowed to register new staking nft
    registry.setStaking(
        staking,
        {'from': registry_owner})

    print('>>> set registry contract in staking')
    # needed to access instance data to check for a bundle
    # if staking/unstaking is possible or not
    staking.setRegistry(
        registry,
        {'from': staking_owner})
    
    if web3.chain_id != 1:
        print('>>> set dip contract in staking')
        staking.setDipContract(
            dip,
            {'from': staking_owner})

    balances_after = get_balances(a)

    # deal with mock setup for testing, playing around
    mock_instance_service = None
    instance_operator = a[INSTANCE_OPERATOR]
    nft_ids = {}
    
    if include_mock_setup:
        chain_id = web3.chain_id

        print('>>> register token {} for chain {}'
            .format(usdt.symbol(), chain_id))

        token_tx = registry.registerToken(
            registry.toChain(chain_id),
            usdt,
            '',
            {'from': registry_owner})
        
        nft_ids[NFT_USDT] = extract_id(token_tx)

        (
            instance_operator,
            mock_instance_service,
            mock_registry
        ) = deploy_mock_instance(a, usdt, publish)

        instance_name = "my instance TEST"
        print('>>> register instance "{}" via instance registry {}'
            .format(instance_name, mock_registry))

        instance_tx = registry.registerInstance(
            mock_registry,
            instance_name,
            '',
            {'from': registry_owner})
        
        wait_for_confirmations(instance_tx)

        nft_ids[NFT_INSTANCE] = extract_id(instance_tx)

        print('>>> register riskpool {}'
            .format(MOCK_RISKPOOL_ID))

        riskpool_tx = registry.registerComponent(
            mock_instance_service.getInstanceId(),
            MOCK_RISKPOOL_ID,
            '',
            {'from': registry_owner})

        wait_for_confirmations(riskpool_tx)

        nft_ids[NFT_RISKPOOL] = extract_id(riskpool_tx)

        bundle_name = 'my bundle TEST'
        bundle_expiry_at = unix_timestamp() + 14 * 24 * 3600

        print('>>> register bundle "{}"/{} for riskpool {}'
            .format(bundle_name, MOCK_BUNDLE_ID, MOCK_RISKPOOL_ID))

        bundle_tx = registry.registerBundle(
            mock_instance_service.getInstanceId(),
            MOCK_RISKPOOL_ID,
            MOCK_BUNDLE_ID,
            bundle_name,
            bundle_expiry_at,
            {'from': registry_owner})

        nft_ids[NFT_BUNDLE] = extract_id(bundle_tx)

        staking_amount = 5000 * 10 ** dip.decimals()
        staker = a[STAKER1]

        if dip.balanceOf(staker) < staking_amount:
            assert web3.chain_id > 1

            missing_funds = staking_amount - dip.balanceOf(staker)
            print('>>> fund staker {} with {} dips'
                .format(staker, missing_funds))
            
            dip.transfer(
                staker,
                missing_funds,
                {'from': instance_operator})

        if dip.allowance(staker, staking.getStakingWallet()) < staking_amount:
            assert web3.chain_id > 1

            print('>>> setting staker {} allowance to {} dips'
                .format(staker, staking_amount))
            
            dip.approve(
                staking,
                staking_amount,
                {'from': staker})

        print('>>> stake {} dip to bundle "{}"/{}'
            .format(staking_amount, bundle_name, MOCK_BUNDLE_ID))

        stake_tx = staking.createStake(
            nft_ids[NFT_BUNDLE],
            staking_amount,
            {'from': staker })

        nft_ids[NFT_STAKE] = extract_id(stake_tx)

    balances_after_mock = get_balances(a)

    delta_registry = get_balance_delta(balances_before, balances_after)
    delta_mock = get_balance_delta(balances_after, balances_after_mock)
    delta_total = get_balance_delta(balances_before, balances_after_mock)

    print('gas costs for registry/staking\n{}'.format(delta_registry))
    print('gas costs for mock setup\n{}'.format(delta_mock))
    print('gas costs total\n{}'.format(delta_total))

    return (
        registry,
        staking,
        nft,
        nft_ids,
        dip,
        usdt,
        mock_instance_service,
        instance_operator,
        registry_owner,
        staking_owner,
        proxy_admin,
    )


def deploy_registry(
    a, # stakeholder accounts
    nft_address=None,
    proxy_admin_address=None,
    publish=False
):
    proxy_admin_owner = a[PROXY_ADMIN_OWNER]
    registry_owner = a[REGISTRY_OWNER]

    proxy_admin = None
    registry = None
    registry_impl = None
    nft = None

    if proxy_admin_address:
        print('>>> obtain contract {} from address {}'
            .format(PROXY_ADMIN_CONTRACT._name, proxy_admin_address))

        proxy_admin = contract_from_address(
            PROXY_ADMIN_CONTRACT,
            proxy_admin_address)

        print('>>> obtain contract {} from address {}'
            .format(REGISTRY_CONTRACT._name, proxy_admin.getProxy()))

        registry_impl = proxy_admin.getImplementation()
        registry = contract_from_address(
            REGISTRY_CONTRACT,
            proxy_admin.getProxy())
    else:
        print('>>> deploy registry implementation contract {}'.format(str(REGISTRY_CONTRACT._name)))
        registry_impl = REGISTRY_CONTRACT.deploy(
            {'from': registry_owner},
            publish_source=publish)

        print('>>> deploy registry proxy admin contract {}'.format(PROXY_ADMIN_CONTRACT._name))
        proxy_admin = deploy_proxy(registry_impl, registry_owner, proxy_admin_owner, publish)

        registry = contract_from_address(
            REGISTRY_CONTRACT, 
            proxy_admin.getProxy())

    if nft_address:
        print('>>> obtain nft contract {} from {}'.format(NFT_CONTRACT._name, nft_address))
        nft = contract_from_address(NFT_CONTRACT, nft_address)
    else:
        print('>>> deploy nft contract {}'.format(NFT_CONTRACT._name))
        nft = NFT_CONTRACT.deploy(
            registry, 
            {'from': registry_owner},
            publish_source=publish)

    if registry.getNft() != ZERO_ADDRESS:
        print('>>> nft contract {} already set in registry'.format(nft))
    else:
        print('>>> set nft contract {} in registry'.format(nft))
        tx = registry.setNftContract(
            nft, 
            registry_owner, 
            {'from': registry_owner})

        # allow sufficient time before next step
        wait_for_confirmations(tx)

    print('>>> done. upgradaple registry at {} with owner {} and implementation {}'
        .format(registry, registry_owner, registry_impl))

    return (
        proxy_admin,
        registry_owner,
        registry,
        nft
    )


def deploy_staking(
    a, # stakeholder accounts
    proxy_admin_address=None,
    publish=False
):
    if proxy_admin_address:
        print('>>> obtain contract {} from address {}'
            .format(PROXY_ADMIN_CONTRACT._name, proxy_admin_address))

        proxy_admin = contract_from_address(
            PROXY_ADMIN_CONTRACT,
                proxy_admin_address)

        print('>>> obtain contract {} from address {}'
            .format(STAKING_CONTRACT._name, proxy_admin.getProxy()))

        staking = contract_from_address(
            STAKING_CONTRACT,
            proxy_admin.getProxy())

        return (
            proxy_admin,
            staking.owner(),
            staking
        )

    proxy_admin_owner = a[PROXY_ADMIN_OWNER]
    registry_owner = a[REGISTRY_OWNER]
    staking_owner = a[STAKING_OWNER]

    print('>>> deploy staking implementation contract {}'.format(STAKING_CONTRACT._name))
    staking_impl = STAKING_CONTRACT.deploy(
        {'from': staking_owner},
        publish_source=publish)

    print('>>> deploy staking proxy admin contract {}'.format(PROXY_ADMIN_CONTRACT._name))
    proxy_admin = deploy_proxy(staking_impl, staking_owner, proxy_admin_owner, publish)
    
    staking = contract_from_address(
        STAKING_CONTRACT, 
        proxy_admin.getProxy())

    print('>>> upgradaple staking at {} with owner {} and implementation {}'
        .format(staking, staking_owner, staking_impl))
    
    return (
        proxy_admin,
        staking_owner,
        staking
    )


def deploy_proxy(
    impl,
    impl_owner,
    proxy_admin_owner,
    publish=False
):

    print('--- (1/3) deploying contract {}'.format(PROXY_ADMIN_CONTRACT._name))
    proxy_admin = PROXY_ADMIN_CONTRACT.deploy(
        impl,
        {'from': proxy_admin_owner},
        publish_source=publish)

    # create call data for deploy step
    oz_proxy_data = proxy_admin.getProxyCallData(
        impl,
        impl_owner,
        proxy_admin_owner)

    print('--- (2/3) deploying contract oz TransparentUpgradeableProxy (=upgradable contract address)')
    oz_proxy = oz.TransparentUpgradeableProxy.deploy(
        impl,
        proxy_admin,
        oz_proxy_data,
        {'from': proxy_admin_owner},
        publish_source=publish)

    print('--- (3/3) setting oz TransparentUpgradeableProxy in contract {}'.format(PROXY_ADMIN_CONTRACT._name))
    tx = proxy_admin.setProxy(
        oz_proxy,
        {'from': proxy_admin_owner})

    # allow sufficient time before next step
    wait_for_confirmations(tx)

    return proxy_admin


def connect_to_dip(a, token, publish=False):
    instance_operator = a[INSTANCE_OPERATOR]

    if web3.chain_id == 1:
        return contract_from_address(
            DIP, 
            DIP_MAINNET_ADDRESS)

    if token:
        return contract_from_address(
            DIP, 
            token)

    print('>>> deploy dummy DIP contract contract')
    dip = DIP.deploy(
        {'from': instance_operator},
        publish_source=publish)

    print('>>> done. dummy DIP contract at {}'.format(dip))
    return dip


def connect_to_usdt(a, token, publish=False):
    instance_operator = a[INSTANCE_OPERATOR]

    if web3.chain_id == 1:
        return contract_from_address(
            USD2, 
            USDT_MAINNET_ADDRESS)

    if token:
        return contract_from_address(
            USD2, 
            token)

    print('>>> deploy dummy USDT contract contract')
    usdt = USD2.deploy(
        {'from': instance_operator},
        publish_source=publish)

    print('>>> done. dummy USDT contract at {}'.format(usdt))
    return usdt


def deploy_mock_instance(
    a,
    usdt, 
    publish=False
):
    instance_operator = a[INSTANCE_OPERATOR]

    print('>>> deploy mock instance service {}'.format(MOCK_INSTANCE_CONTRACT._name))
    mock_instance_service = MOCK_INSTANCE_CONTRACT.deploy(
        {'from': instance_operator},
        publish_source=publish)

    mock_registry = contract_from_address(
        MOCK_REGISTRY_CONTRACT,
        mock_instance_service.getRegistry())

    print('>>> mock instance service at {} registry at {}'
        .format(mock_instance_service, mock_registry))

    # create instance mock setup
    type_riskpool = 2
    component_state_active = 3

    print('>>> mock active riskpool {} on instance'
        .format(MOCK_RISKPOOL_ID))

    mock_instance_service.setComponentInfo(
        MOCK_RISKPOOL_ID,
        type_riskpool,
        component_state_active,
        usdt)

    bundle_name = 'my test bundle'
    bundle_state_active = 0
    bundle_funding = 10000 * 10 ** usdt.decimals()

    print('>>> mock active bundle "" (id={}) for riskpool {}'
        .format(bundle_name, MOCK_RISKPOOL_ID))

    mock_instance_service.setBundleInfo(
        MOCK_BUNDLE_ID,
        MOCK_RISKPOOL_ID,
        bundle_state_active,
        bundle_funding)

    return (
        instance_operator,
        mock_instance_service,
        mock_registry
    )


def verify_deploy(
    stakeholder_accounts,
    registry_contract_address,
    staking_contract_address,
    dip_address,
):
    # define stakeholder accounts
    a = stakeholder_accounts


def extract_id(tx):
    assert 'LogChainRegistryObjectRegistered' in tx.events
    return dict(tx.events['LogChainRegistryObjectRegistered'])['id']


def get_balance_sum(b1, b2):
    d = {}

    for a in b1:
        d[a] = b1[a] + b2[a]
    
    return d


def get_balance_delta(b1, b2):
    d = {}
    total = 0

    for a in b1:
        amount = b1[a] - b2[a]
        total += amount

        d[a] = amount
    
    d['total'] = total
    d['total_eth_at_20gwei'] = '{:.5f}'.format((total * 20 * 10**9)/10**18)

    return d


def get_balances(stakeholder_accounts):
    b = {}

    for a in stakeholder_accounts.keys():
        b[a] = stakeholder_accounts[a].balance()
    
    return b


