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
    MockRegistry,
    OwnableProxyAdmin,
    ChainRegistryV01,
    StakingV01,
)

from scripts.const import ZERO_ADDRESS
from scripts.util import (
    contract_from_address,
    unix_timestamp
)

RISKPOOL_ID = 1
BUNDLE_ID = 1
BUNDLE_FUNDING = 10000

BUNDLE_STATE_ACTIVE = 0
BUNDLE_STATE_LOCKED = 1
BUNDLE_STATE_CLOSED = 2
BUNDLE_STATE_BURNED = 3

# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_stake_and_unstake_happy_path(
    mockInstance: MockInstance,
    mockRegistry: MockRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    dip: DIP,
    instanceOperator: Account,
    stakingV01: StakingV01,
    stakingOwner: Account,
    staker: Account,
    theOutsider: Account
):
    bundle_nft = create_mock_bundle_setup(
        mockInstance,
        mockRegistry,
        usd2,
        proxyAdmin,
        proxyAdminOwner,
        chainRegistryV01,
        registryOwner,
        theOutsider)
    
    assert bundle_nft > 0

    # prepare reward rate: 20.0% apr
    reward_rate = stakingV01.toRate(20, -2)
    stakingV01.setRewardRate(reward_rate, {'from': stakingOwner})
    assert stakingV01.rewardRate() == reward_rate

    # prepare staker
    staking_amount = 100000 * 10 ** dip.decimals()
    prepare_staker(staker, staking_amount, dip, instanceOperator, stakingV01)

    staking_tx = stakingV01.createStake(
        bundle_nft,
        staking_amount,
        {'from': staker })

    # check balances after staking
    assert dip.balanceOf(staker) == 0
    assert dip.balanceOf(stakingV01.getStakingWallet()) == staking_amount

    # get stake nft id
    created_at = web3.eth.getBlock(web3.eth.block_number)['timestamp']
    assert 'LogStakingStaked' in staking_tx.events
    evt = staking_tx.events['LogStakingStaked']
    nft_id = evt['id']

    # check if unstaking is supported
    assert stakingV01.isUnstakingSupported(bundle_nft) is False

    with brownie.reverts('ERROR:STK-250:UNSTAKE_NOT_SUPPORTED'):
        stakingV01.unstake(nft_id, 1, {'from': staker })

    # close bundle
    mockInstance.setBundleInfo(
        BUNDLE_ID,
        RISKPOOL_ID,
        BUNDLE_STATE_CLOSED,
        BUNDLE_FUNDING * 10 ** dip.decimals())

    assert stakingV01.isUnstakingSupported(bundle_nft) is True

    unstake_amount = int(staking_amount / 3)
    unstake_tx = stakingV01.unstake(nft_id, unstake_amount, {'from': staker })

    # check balances after unstaking
    assert dip.balanceOf(staker) == unstake_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()) == staking_amount - unstake_amount

    assert 'LogStakingUnstaked' in unstake_tx.events
    evt = dict(unstake_tx.events['LogStakingUnstaked'])
    assert evt['id'] == nft_id
    assert evt['target'] == bundle_nft
    assert evt['user'] == staker
    assert evt['amount'] == unstake_amount
    assert evt['newBalance'] == staking_amount - unstake_amount

    # check staking info for nft after unstaking
    info = stakingV01.getInfo(nft_id).dict()
    updated_at = web3.eth.getBlock(web3.eth.block_number)['timestamp']
    assert info['id'] == nft_id
    assert info['target'] == bundle_nft
    assert info['stakeBalance'] == staking_amount - unstake_amount
    assert info['createdAt'] == created_at
    assert info['updatedAt'] == updated_at


def delta_is_tiny(a, b, epsilon=10 ** -10):
    return abs(1 - (a / b)) < 10 ** -10


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
    mockRegistry: MockRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account
) -> int:
    # setup attributes
    chain_id = chainRegistryV01.toChain(mockInstance.getChainId())
    instance_id = mockInstance.getInstanceId()
    bundle_name = 'my test bundle'
    bundle_funding = BUNDLE_FUNDING * 10 ** usd2.decimals()
    bundle_expiry_at = unix_timestamp() + 14 * 24 * 3600

    # setup mock instance
    type_riskpool = 2

    state_created = 0
    state_active = 3
    state_paused = 4

    mockInstance.setComponentInfo(
        RISKPOOL_ID,
        type_riskpool,
        state_active,
        usd2)

    bundle_state_active = 0 # enum BundleState { Active, Locked, Closed, Burned }
    mockInstance.setBundleInfo(
        BUNDLE_ID,
        RISKPOOL_ID,
        BUNDLE_STATE_ACTIVE,
        bundle_funding)

    # register token
    tx_token = chainRegistryV01.registerToken(
            chain_id,
            usd2,
            {'from': registryOwner})

    # register instance
    tx_instance = chainRegistryV01.registerInstance(
        mockRegistry,
        "mockRegistry TEST",
        {'from': registryOwner})

    # register riskpool
    tx_riskpool = chainRegistryV01.registerComponent(
        instance_id,
        RISKPOOL_ID,
        {'from': registryOwner})

    # register bundle
    tx_bundle = chainRegistryV01.registerBundle(
        instance_id,
        RISKPOOL_ID,
        BUNDLE_ID,
        bundle_name,
        bundle_expiry_at,
        {'from': theOutsider})

    nft_id = chainRegistryV01.getBundleNftId(instance_id, BUNDLE_ID)

    return nft_id
