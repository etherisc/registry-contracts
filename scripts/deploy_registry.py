from brownie.network import accounts
from brownie.network.account import Account

from brownie import (
    interface,
    network,
    web3,
    DIP,
    USD1,
    USD2,
    MockInstance,
    MockRegistry,
    OwnableProxyAdmin,
    ChainNft,
    ChainRegistryV01,
    StakingV01,
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
    GIF_ACTOR
)

GAS_PRICE_SAFETY_FACTOR = 2
GAS_REGISTRY = {
    INSTANCE_OPERATOR: 1500000, # dip,usdt token for testnets
    PROXY_ADMIN_OWNER: 3700000, # proxy adins for registry, staking
    REGISTRY_OWNER: 5700000, # registry contract, some wiring
    STAKING_OWNER: 4200000, # staking contract, some wiring
    STAKER1: 0
}

GAS_MOCK = {
    INSTANCE_OPERATOR: 1200000, # mock instance and instance registry, some transfers
    PROXY_ADMIN_OWNER: 0, # proxy adins for registry, staking
    REGISTRY_OWNER: 1800000, # registration of protocol, chain, token, instance, riskpool, bundle
    STAKING_OWNER: 0,
    STAKER1: 700000, # create bundle stake
}

PROXY_ADMIN_CONTRACT = OwnableProxyAdmin
NFT_CONTRACT = ChainNft
REGISTRY_CONTRACT = ChainRegistryV01
STAKING_CONTRACT = StakingV01

MOCK_INSTANCE_CONTRACT = MockInstance
MOCK_REGISTRY_CONTRACT = MockRegistry

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
    print('from scripts.deploy_registry import all_in_1, get_accounts, get_stakeholder_accounts, check_funds, amend_funds, verify_deploy, help')
    print('a = get_accounts()')
    print('stakeholder_accounts = get_stakeholder_accounts(a)')
    print('check_funds(stakeholder_accounts)')
    print('(registry, staking, nft, nft_ids, dip, usdt, instance_service, instance_operator, registry_owner, staking_owner, proxy_admin) = all_in_1(stakeholder_accounts)')
    print('instance_service.getBundle({}).dict()'.format(MOCK_BUNDLE_ID))
    print("registry.getNftInfo(nft['stake']).dict()")
    print("registry.decodeStakeData(nft['stake']).dict()")
    print("staking.getInfo(nft['stake']).dict()")


def actor_account(actor, accts):
    assert actor in GIF_ACTOR
    account_idx = GIF_ACTOR[actor]
    return accts[account_idx]


def get_stakeholder_accounts(accts):
    if len(accts) >= 20:
        return {
            INSTANCE_OPERATOR: actor_account(INSTANCE_OPERATOR, accts),
            PROXY_ADMIN_OWNER: actor_account(PROXY_ADMIN_OWNER, accts),
            REGISTRY_OWNER: actor_account(REGISTRY_OWNER, accts),
            STAKING_OWNER: actor_account(STAKING_OWNER, accts),
            STAKER1: actor_account(STAKER1, accts),
        }
    
    print('ERROR: current chain is {}. len(accounts): {}, expected 20'
        .format(web3.chain_id, len(accts)))

    return {
        INSTANCE_OPERATOR: None,
        PROXY_ADMIN_OWNER: None,
        REGISTRY_OWNER: None,
        STAKING_OWNER: None,
        STAKER1: None,
    }


def get_accounts(mnemonic=None):
    if not mnemonic and len(accounts) >= 20:
        return accounts
    
    if mnemonic:
        return accounts.from_mnemonic(mnemonic, count=20)
    
    print('ERROR: mnemonic is mandatory on chains without prefilled accounts (len => 20)')
    return None


def get_gas_price():
    if web3.eth.chain_id == 1337:
        return 1
    
    return web3.eth.gas_price


def amend_funds(
    stakeholder_accounts,
    gas_price=None,
    safety_factor=GAS_PRICE_SAFETY_FACTOR,
    include_mock_setup=True
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
    include_mock_setup=True
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
    
    g_missing = 0
    for s in a.keys():
        bs = a[s].balance()
        if bs >= gp * g[s]:
            print('{}.balance(): {} OK'.format(s, bs))
        else:
            ms = gp * g[s] - bs
            print('{}.balance(): {} MISSING: {}'.format(s, bs, ms))
            g_missing += ms

    if g_missing > 0:
        if a[INSTANCE_OPERATOR].balance() >= gp * g[INSTANCE_OPERATOR] + g_missing:
            print('{} balance sufficient to fund other accounts, use amend_funds(a) and try again'.format(INSTANCE_OPERATOR))
        else:
            print('{} balance insufficient to fund other accounts. missing amount: {}'
                .format(INSTANCE_OPERATOR, g_missing))
    
    assert g_missing == 0


def all_in_1(
    stakeholder_accounts,
    dip_address=None,
    usdt_address=None,
    include_mock_setup=True,
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
    ) = deploy_registry(a, dip, publish)

    (
        proxy_admin, 
        staking_owner,
        staking
    ) = deploy_staking(a, registry, dip, publish)

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

        nft_ids[NFT_INSTANCE] = extract_id(instance_tx)

        print('>>> register riskpool {}'
            .format(MOCK_RISKPOOL_ID))

        riskpool_tx = registry.registerComponent(
            mock_instance_service.getInstanceId(),
            MOCK_RISKPOOL_ID,
            '',
            {'from': registry_owner})

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
    dip_address,
    publish=False
):
    proxy_admin_owner = a[PROXY_ADMIN_OWNER]
    registry_owner = a[REGISTRY_OWNER]

    print('>>> deploy registry implementation contract {}'.format(str(REGISTRY_CONTRACT._name)))
    registry_impl = REGISTRY_CONTRACT.deploy(
        {'from': registry_owner},
        publish_source=publish)

    print('>>> deploy registry proxy admin contract {}'.format(PROXY_ADMIN_CONTRACT._name))
    proxy_admin = deploy_proxy(registry_impl, registry_owner, proxy_admin_owner, publish)

    registry = contract_from_address(
        REGISTRY_CONTRACT, 
        proxy_admin.getProxy())

    print('>>> deploy nft contract {}'.format(NFT_CONTRACT._name))
    nft = NFT_CONTRACT.deploy(
        registry, 
        {'from': registry_owner},
        publish_source=publish)

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
    registry,
    dip,
    publish=False
):
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

    print('>>> set staking contract in registry')
    # needed for onlyStaking modifier
    # context only staking is allowed to register new staking nft
    registry.setStakingContract(
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

    proxy_admin = PROXY_ADMIN_CONTRACT.deploy(
        impl,
        # impl_owner,
        {'from': proxy_admin_owner},
        publish_source=publish)

    # create call data for deploy step
    oz_proxy_data = proxy_admin.getProxyCallData(
        impl,
        impl_owner,
        proxy_admin_owner)

    # deploy
    oz_proxy = oz.TransparentUpgradeableProxy.deploy(
        impl,
        proxy_admin,
        oz_proxy_data,
        {'from': proxy_admin_owner},
        publish_source=publish)

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
            TETHER_MAINNET_ADDRESS)

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

    for a in b1:
        d[a] = b1[a] - b2[a]
    
    return d


def get_balances(stakeholder_accounts):
    b = {}

    for a in stakeholder_accounts.keys():
        b[a] = stakeholder_accounts[a].balance()
    
    return b


