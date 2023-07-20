import pytest
import brownie

from brownie.network.account import Account

from brownie import (
    chain,
    history,
    interface,
    web3,
    USD1,
    USD2,
    DIP,
    MockInstance,
    MockInstanceRegistry,
    OwnableProxyAdmin,
    ChainRegistryV01,
    StakingV01,
    StakingV03,
)

from scripts.const import ZERO_ADDRESS
from scripts.util import (
    contract_from_address,
    unix_timestamp
)

# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_create_stake_v3_happy_path(
    stakingProxyAdmin: OwnableProxyAdmin,
    mockInstance: MockInstance,
    mockRegistry: MockInstanceRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    dip: DIP,
    instanceOperator: Account,
    stakingV01: StakingV03,
    stakingOwner: Account,
    staker: Account,
    theOutsider: Account
):

    registry = contract_from_address(ChainRegistryV01, stakingV01.getRegistry())

    bundle_lifetime = 100 * 24 * 3600
    bundle_nft = create_mock_bundle_setup(
        mockInstance,
        mockRegistry,
        usd2,
        proxyAdmin,
        proxyAdminOwner,
        chainRegistryV01,
        registryOwner,
        theOutsider,
        bundle_lifetime=bundle_lifetime)
    
    assert bundle_nft > 0

    # attempt to stake
    staking_amount = 5000 * 10 ** dip.decimals()
    prepare_staker(staker, 2 * staking_amount, dip, instanceOperator, stakingV01)

    # check balances before staking
    assert dip.balanceOf(staker) == 2 * staking_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()) == 0

    staking_tx = stakingV01.createStake(
        bundle_nft,
        staking_amount,
        {'from': staker })

    # check balances after staking
    assert dip.balanceOf(staker) == staking_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()) == staking_amount

    # check staking balance event
    assert 'LogStakingStaked' in staking_tx.events
    evt = staking_tx.events['LogStakingStaked']
    nft_id = evt['id']
    assert evt['target'] == bundle_nft
    assert evt['user'] == staker
    assert evt['amount'] == staking_amount
    assert evt['newBalance'] == staking_amount

    # check staking nft
    assert 'LogStakingNewStakeCreated' in staking_tx.events
    evt = staking_tx.events['LogStakingNewStakeCreated']
    assert evt['target'] == bundle_nft
    assert evt['user'] == staker
    assert evt['id'] == nft_id

    # check nft info in registry
    assert chainRegistryV01.ownerOf(nft_id) == staker

    state_approved = 2 # ObjectState { Undefined, Proposed, Approved, ...}
    info = chainRegistryV01.getNftInfo(nft_id).dict()
    assert info['id'] == nft_id
    assert info['objectType'] == chainRegistryV01.STAKE()
    assert info['state'] == state_approved
    assert info['version'] == chainRegistryV01.version()
    (target_id, target_type) = chainRegistryV01.decodeStakeData(nft_id)
    assert target_id == bundle_nft
    assert target_type == chainRegistryV01.BUNDLE()

    # get bundle expiry at
    expiry_at = registry.decodeBundleData(bundle_nft).dict()['expiryAt']
    assert abs(expiry_at - (mockInstance.getBundle(1).dict()['createdAt'] + bundle_lifetime)) <= 2

    # check staking info for nft
    info = stakingV01.getInfo(nft_id).dict()
    block_timestamp = web3.eth.getBlock(web3.eth.block_number)['timestamp']
    assert info['id'] == nft_id
    assert info['target'] == bundle_nft
    assert info['stakeBalance'] == staking_amount
    assert info['rewardBalance'] == 0
    assert info['createdAt'] == block_timestamp
    assert info['updatedAt'] == block_timestamp
    assert info['lockedUntil'] == expiry_at
    assert info['version'] == stakingV01.version()

    # assert False


def prepare_staker(
    staker,
    staking_amount,
    dip,
    instanceOperator,
    stakingV01
):
    dip.transfer(staker, staking_amount, {'from': instanceOperator })
    dip.approve(stakingV01.getStakingWallet(), staking_amount, {'from': staker })


def create_mock_bundle_setup(
    mockInstance: MockInstance,
    mockRegistry: MockInstanceRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account,
    bundle_lifetime = 14 * 24 * 3600
) -> int:
    # setup attributes
    chain_id = chainRegistryV01.toChain(mockInstance.getChainId())
    instance_id = mockInstance.getInstanceId()
    riskpool_id = 1
    bundle_id = 1
    bundle_name = 'my test bundle'
    bundle_funding = 10000 * 10 ** usd2.decimals()
    bundle_expiry_at = unix_timestamp() + bundle_lifetime

    # setup mock instance
    type_riskpool = 2

    state_created = 0
    state_active = 3
    state_paused = 4

    mockInstance.setComponentInfo(
        riskpool_id,
        type_riskpool,
        state_active,
        usd2)

    bundle_state_active = 0 # enum BundleState { Active, Locked, Closed, Burned }
    mockInstance.setBundleInfo(
        bundle_id,
        riskpool_id,
        bundle_state_active,
        bundle_funding)

    # register token
    tx_token = chainRegistryV01.registerToken(
            chain_id,
            usd2,
            '',
            {'from': registryOwner})

    # register instance
    tx_instance = chainRegistryV01.registerInstance(
        mockRegistry,
        'mockRegistry TEST',
        '',
        {'from': registryOwner})

    # register riskpool
    tx_riskpool = chainRegistryV01.registerComponent(
        instance_id,
        riskpool_id,
        '',
        {'from': registryOwner})

    # register bundle
    tx_bundle = chainRegistryV01.registerBundle(
        instance_id,
        riskpool_id,
        bundle_id,
        bundle_name,
        bundle_expiry_at,
        {'from': theOutsider})

    nft_id = chainRegistryV01.getBundleNftId(instance_id, bundle_id)

    return nft_id
