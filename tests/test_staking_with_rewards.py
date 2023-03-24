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


def test_stake_bundle_happy_path(
    mockInstance: MockInstance,
    mockRegistry: MockInstanceRegistry,
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
        theOutsider,
        bundle_lifetime = int(stakingV01.YEAR_DURATION() * 0.6666))
    
    assert bundle_nft > 0

    # prepare reward rate: 20.0% apr
    reward_rate = stakingV01.toRate(20, -2)
    stakingV01.setRewardRate(reward_rate, {'from': stakingOwner})
    assert stakingV01.rewardRate() == reward_rate

    # prepare staker
    staking_amount = 100000 * 10 ** dip.decimals()
    prepare_staker(staker, 2 * staking_amount, dip, instanceOperator, stakingV01)

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

    # check staking info for nft right after creation of stake
    info = stakingV01.getInfo(nft_id).dict()
    created_at = web3.eth.getBlock(web3.eth.block_number)['timestamp']
    assert info['id'] == nft_id
    assert info['target'] == bundle_nft
    assert info['stakeBalance'] == staking_amount
    assert info['rewardBalance'] == 0
    assert info['createdAt'] == created_at
    assert info['updatedAt'] == created_at

    # wait for quarter of a year (20% apr -> 5% for a quarter year)
    quarter_year = int(stakingV01.YEAR_DURATION() / 4)
    chain.sleep(quarter_year)
    chain.mine(1)

    # increase stake to force reward calculation
    increase_tx = stakingV01.stake(
        nft_id,
        staking_amount,
        {'from': staker })

    # calculate expected reward amount
    updated_at = web3.eth.getBlock(web3.eth.block_number)['timestamp']
    year_fraction = (updated_at - created_at) / stakingV01.YEAR_DURATION()
    expected_reward_amount = int(staking_amount * 0.2 * year_fraction)

    #  check event
    assert 'LogStakingRewardsUpdated' in increase_tx.events
    evt = increase_tx.events['LogStakingRewardsUpdated']
    assert evt['id'] == nft_id
    assert delta_is_tiny(evt['amount'], expected_reward_amount)
    assert delta_is_tiny(evt['newBalance'], expected_reward_amount)

    # check info update
    info = stakingV01.getInfo(nft_id).dict()
    assert info['id'] == nft_id
    assert info['target'] == bundle_nft
    assert info['stakeBalance'] == 2 * staking_amount
    assert delta_is_tiny(info['rewardBalance'], expected_reward_amount)
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
    bundle_lifetime
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
