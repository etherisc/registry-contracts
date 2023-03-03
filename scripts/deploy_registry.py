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
    ChainRegistryV01,
    StakingV01,
)

from scripts.util import (
    get_package,
    contract_from_address,
    unix_timestamp
)

from scripts.const import (
    DIP_MAINNET_ADDRESS,
    USDT_MAINNET_ADDRESS,
    ACCOUNTS_MNEMONIC,
    INSTANCE_OPERATOR,
    # INSTANCE_WALLET,
    # ORACLE_PROVIDER,
    # CHAINLINK_NODE_OPERATOR,
    # RISKPOOL_KEEPER,
    # RISKPOOL_WALLET,
    # INVESTOR,
    # PRODUCT_OWNER,
    # INSURER,
    # CUSTOMER1,
    # CUSTOMER2,
    REGISTRY_OWNER,
    STAKING_OWNER,
    PROXY_ADMIN_OWNER,
    STAKER1,
    STAKER2,
    OUTSIDER,
    GIF_ACTOR
)

PROXY_ADMIN_CONTRACT = OwnableProxyAdmin
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

def help():
    print('from scripts.deploy_registry import all_in_1, verify_deploy, help')
    print('(registry, staking, nft, dip, usdt, instance_service, instance_operator, registry_owner, staking_owner, proxy_admin) = all_in_1()')
    print('instance_service.getBundle({}).dict()'.format(MOCK_BUNDLE_ID))
    print("registry.getNftInfo(nft['stake']).dict()")
    print("registry.decodeStakeData(nft['stake']).dict()")
    print("staking.getInfo(nft['stake']).dict()")


def actor_account(actor):
    assert actor in GIF_ACTOR
    account_idx = GIF_ACTOR[actor]
    return accounts[account_idx]


def accounts_ganache():
    return {
        INSTANCE_OPERATOR: actor_account(INSTANCE_OPERATOR),
        PROXY_ADMIN_OWNER: actor_account(PROXY_ADMIN_OWNER),
        REGISTRY_OWNER: actor_account(REGISTRY_OWNER),
        STAKING_OWNER: actor_account(STAKING_OWNER),
        STAKER1: actor_account(STAKER1),
    }


def all_in_1(
    stakeholder_accounts=accounts_ganache(),
    include_mock_setup=True,
    publish=False
):
    # check stakeholder accounts
    a = stakeholder_accounts
    assert INSTANCE_OPERATOR in a
    assert PROXY_ADMIN_OWNER in a
    assert REGISTRY_OWNER in a
    assert STAKING_OWNER in a
    assert STAKER1 in a

    dip = connect_to_dip(a, publish)
    usdt = connect_to_usdt(a, publish)

    (
        proxy_admin, 
        registry_owner,
        registry
    ) = deploy_registry(a, publish)

    (
        proxy_admin, 
        staking_owner,
        staking
    ) = deploy_staking(a, registry, dip, publish)

    # deal with mock setup for testing, playing around
    nft = None
    mock_instance_service = None

    if include_mock_setup:
        nft = {}
        chain_id = web3.chain_id

        print('>>> register token {} for chain {}'
            .format(usdt.symbol(), chain_id))

        token_tx = registry.registerToken(
            registry.toChain(chain_id),
            usdt,
            {'from': registry_owner})
        
        nft[NFT_USDT] = extract_id(token_tx)

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
            {'from': registry_owner})

        nft[NFT_INSTANCE] = extract_id(instance_tx)

        print('>>> register riskpool {}'
            .format(MOCK_RISKPOOL_ID))

        riskpool_tx = registry.registerComponent(
            mock_instance_service.getInstanceId(),
            MOCK_RISKPOOL_ID,
            {'from': registry_owner})

        nft[NFT_RISKPOOL] = extract_id(riskpool_tx)

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

        nft[NFT_BUNDLE] = extract_id(bundle_tx)

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
                staking.getStakingWallet(),
                staking_amount,
                {'from': staker})

        print('>>> stake {} dip to bundle "{}"/{}'
            .format(staking_amount, bundle_name, MOCK_BUNDLE_ID))

        stake_tx = staking.createStake(
            nft[NFT_BUNDLE],
            staking_amount,
            {'from': staker })

        nft[NFT_STAKE] = extract_id(stake_tx)

    return (
        registry,
        staking,
        nft,
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
    proxy_admin = PROXY_ADMIN_CONTRACT.deploy(
        registry_impl,
        registry_owner,
        {'from': proxy_admin_owner},
        publish_source=publish)

    registry = contract_from_address(
        REGISTRY_CONTRACT, 
        proxy_admin.getProxy())

    print('>>> done. upgradaple registry at {} with owner {}'
        .format(registry, registry_owner))

    return (
        proxy_admin,
        registry_owner,
        registry
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
    proxy_admin = PROXY_ADMIN_CONTRACT.deploy(
        staking_impl,
        staking_owner,
        {'from': proxy_admin_owner},
        publish_source=publish)
    
    staking = contract_from_address(
        STAKING_CONTRACT, 
        proxy_admin.getProxy())

    print('>>> upgradaple staking at {} with owner {}'
        .format(staking, staking_owner))

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


def connect_to_dip(a, publish=False):
    instance_operator = a[INSTANCE_OPERATOR]

    if web3.chain_id == 1:
        return contract_from_address(
            DIP, 
            DIP_MAINNET_ADDRESS)

    print('>>> deploy dummy DIP contract contract')
    dip = DIP.deploy(
        {'from': instance_operator},
        publish_source=publish)

    print('>>> done. dummy DIP contract at {}'.format(dip))
    return dip


def connect_to_usdt(a, publish=False):
    instance_operator = a[INSTANCE_OPERATOR]

    if web3.chain_id == 1:
        return contract_from_address(
            USD2, 
            TETHER_MAINNET_ADDRESS)

    print('>>> deploy dummy DIP contract contract')
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
