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


def test_create_stake_v3(
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


def test_unstake_v3(
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

    bundle_lifetime = stakingV01.YEAR_DURATION() / 2
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

    staking_tx = stakingV01.createStake(
        bundle_nft,
        staking_amount,
        {'from': staker })

    # get stake nft
    stake_nft = staking_tx.events['LogStakingNewStakeCreated']['id']

    # check balances after staking
    assert dip.balanceOf(staker) == staking_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()) == staking_amount

    # add reward reserves
    dip.approve(stakingV01, staking_amount, {'from': instanceOperator})
    stakingV01.refillRewardReserves(staking_amount, {'from': instanceOperator})

    # check isUnstakeingAvailable
    assert stakingV01.isUnstakingAvailable(stake_nft) is False
    assert stakingV01.isUnstakingSupported(bundle_nft) is False

    # attempt to unstake leads to revert
    with brownie.reverts('ERROR:STK-250:UNSTAKE_NOT_SUPPORTED'):
        stakingV01.unstakeAndClaimRewards(stake_nft, {'from': staker})

    # move time forward
    bundle_expiry = registry.decodeBundleData(bundle_nft).dict()['expiryAt']
    seconds = bundle_expiry - chain.time() + 1
    chain.sleep(seconds)
    chain.mine(1)

    # check isUnstakeingAvailable
    stake_info = stakingV01.getInfo(stake_nft).dict()
    assert chain.time() >= bundle_expiry
    assert chain.time() >= stake_info['lockedUntil']
    assert stakingV01.isUnstakingAvailable(stake_nft) is True
    assert stakingV01.isUnstakingSupported(bundle_nft) is True

    # check rewards
    reward_rate = stakingV01.toRate(20,-2)
    stakingV01.setTargetRewardRate(bundle_nft, reward_rate, {'from': stakingOwner})
    stake_info = stakingV01.getInfo(stake_nft)
    rewards = stakingV01.calculateRewardsIncrement(stake_info)
    rewards_expected = int(reward_rate/10**stakingV01.decimals() * bundle_lifetime/stakingV01.YEAR_DURATION() * stake_info['stakeBalance'])
    assert abs(1.0 - rewards/rewards_expected) < 10**-6
    assert stake_info.dict()['rewardBalance'] == 0

    # attempt to just update rewards as non-owner
    with brownie.reverts('Ownable: caller is not the owner'):
        stakingV01.updateRewards(stake_nft, {'from':staker})

    # update rewards as owner
    tx = stakingV01.updateRewards(stake_nft, {'from':stakingOwner})

    assert 'LogStakingRewardsUpdated' in tx.events
    rewards = tx.events['LogStakingRewardsUpdated']['amount']

    stake_info = stakingV01.getInfo(stake_nft)
    assert stake_info.dict()['rewardBalance'] == rewards
    assert abs(1.0 - rewards/rewards_expected) < 10**-6

    # full unstake
    tx = stakingV01.unstakeAndClaimRewards(stake_nft, {'from': staker})

    assert 'LogStakingRewardsUpdated' in tx.events
    assert 'LogStakingUnstaked' in tx.events
    assert 'LogStakingRewardsClaimed' in tx.events

    rewards_increment = tx.events['LogStakingRewardsUpdated']['amount']
    assert rewards_increment/rewards < 10**-6
    assert tx.events['LogStakingUnstaked']['amount'] == staking_amount
    assert tx.events['LogStakingRewardsClaimed']['amount'] == rewards + rewards_increment

    assert dip.balanceOf(staker) == 2 * staking_amount + rewards + rewards_increment


def test_restake(
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

    # set default reward rate to 12.5%
    apr_12_5 = stakingV01.toRate(125, -3)
    stakingV01.setRewardRate(apr_12_5, {'from': stakingOwner})

    # provide some reward reserves
    reward_reserves_amount = 1000*10**dip.decimals()
    dip.approve(stakingV01, reward_reserves_amount, {'from': instanceOperator})
    stakingV01.refillRewardReserves(reward_reserves_amount, {'from': instanceOperator})

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
        bundle_lifetime = bundle_lifetime)

    bundle_nft2 = create_mock_bundle_setup(
        mockInstance,
        mockRegistry,
        usd2,
        proxyAdmin,
        proxyAdminOwner,
        chainRegistryV01,
        registryOwner,
        theOutsider,
        bundle_lifetime = 2*bundle_lifetime,
        bundle_id = 2,
        is_first_bundle = False)
    
    assert bundle_nft > 0
    assert bundle_nft2 > 0
    assert bundle_nft != bundle_nft2

    # attempt to stake
    staking_amount = 5000 * 10 ** dip.decimals()
    prepare_staker(staker, 2 * staking_amount, dip, instanceOperator, stakingV01)

    # check balances before staking
    assert dip.balanceOf(staker) == 2 * staking_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()) == reward_reserves_amount

    staking_tx = stakingV01.createStake(
        bundle_nft,
        staking_amount,
        {'from': staker })

    assert 'LogStakingNewStakeCreated' in staking_tx.events
    stake_id = staking_tx.events['LogStakingNewStakeCreated']['id']

    assert stakingV01.stakes(bundle_nft) == staking_amount
    assert stakingV01.stakes(bundle_nft2) == 0

    # get balances
    staking_balance1 = stakingV01.stakeBalance()
    reward_reserves1 = stakingV01.rewardReserves()
    total_balance1 = staking_balance1 + reward_reserves1
    wallet_balance1 = dip.balanceOf(stakingV01.getStakingWallet())
    assert total_balance1 == wallet_balance1

    # attempt to trigger restaking by somebody else than owner
    with brownie.reverts("ERROR:STK-010:USER_NOT_OWNER"):
        stakingV01.restake(stake_id, bundle_nft2, {'from': theOutsider})

    # attempt to restake too early
    with brownie.reverts("ERROR:STK-150:UNSTAKING_NOT_SUPPORTED"):
        stakingV01.restake(stake_id, bundle_nft2, {'from': staker})

    sleep_time = bundle_lifetime + 1
    chain.sleep(sleep_time)
    chain.mine(1)

    # check that bundle stakes remain the same
    assert stakingV01.stakes(bundle_nft) == staking_amount
    assert stakingV01.stakes(bundle_nft2) == 0

    # attempt to restake to something else than a bundle
    with brownie.reverts("ERROR:STK-151:STAKING_NOT_SUPPORTED"):
        stakingV01.restake(stake_id, stake_id, {'from': staker})

    info = stakingV01.getInfo(stake_id)
    stake_balance = info.dict()['stakeBalance']
    reward_balance = info.dict()['rewardBalance'] + stakingV01.calculateRewardsIncrement(info)
    restake_amount = stake_balance + reward_balance

    # restake as designed/intended
    restake_tx = stakingV01.restake(stake_id, bundle_nft2, {'from': staker})

    assert 'LogStakingRestaked' in restake_tx.events
    stake_id2 = restake_tx.events['LogStakingRestaked']['stakeId']

    # check that bundle stakes have been properly updated
    assert stakingV01.stakes(bundle_nft) == 0
    assert abs(stakingV01.stakes(bundle_nft2) - restake_amount)/10**dip.decimals() < 10**-4

    # get balances after restake
    staking_balance2 = stakingV01.stakeBalance()
    reward_reserves2 = stakingV01.rewardReserves()
    total_balance2 = staking_balance2 + reward_reserves2
    wallet_balance2 = dip.balanceOf(stakingV01.getStakingWallet())

    assert reward_reserves1 > reward_reserves2
    assert staking_balance1 < staking_balance2
    assert reward_reserves1 - reward_reserves2 == staking_balance2 - staking_balance1

    assert total_balance2 == wallet_balance2
    assert total_balance2 == total_balance1

# TODO: mz reenable those tests
@pytest.mark.skip()
def test_target_reward_rate(
    mockInstance: MockInstance,
    mockRegistry: MockInstanceRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    dip: DIP,
    stakingV01: StakingV01,
    stakingOwner: Account,
    staker: Account,
    theOutsider: Account
):
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

    # check initial reward rate setting
    assert stakingV01.rewardRate() == 0
    assert stakingV01.getTargetRewardRate(bundle_nft) == 0

    # set default rate to 5%
    default_rate = stakingV01.toRate(5, -2)
    stakingV01.setRewardRate(default_rate, {'from': stakingOwner})

    # check new reward rate setting
    assert stakingV01.rewardRate() == default_rate
    assert stakingV01.getTargetRewardRate(bundle_nft) == default_rate

    # set bundle specific rate of 7.5%
    bundle_rate = stakingV01.toRate(75, -3)

    # attempt to set target rate as non owner
    with brownie.reverts('Ownable: caller is not the owner'):
        stakingV01.setTargetRewardRate(bundle_nft, bundle_rate, {'from': theOutsider})

    # set target rate as owner
    tx = stakingV01.setTargetRewardRate(bundle_nft, bundle_rate, {'from': stakingOwner})

    # check log entry
    assert 'LogTargetRewardRateSet' in tx.events

    evt = tx.events['LogTargetRewardRateSet']
    assert evt['user'] == stakingOwner
    assert evt['target'] == bundle_nft
    assert evt['oldRewardRate'] == default_rate
    assert evt['newRewardRate'] == bundle_rate

    # check new reward rate setting
    assert stakingV01.rewardRate() == default_rate
    assert stakingV01.getTargetRewardRate(bundle_nft) == bundle_rate

    # set new bundle specific rate of 0%
    bundle_rate_zero = 0
    tx = stakingV01.setTargetRewardRate(bundle_nft, bundle_rate_zero, {'from': stakingOwner})

    # check new reward rate setting
    assert stakingV01.rewardRate() == default_rate
    assert stakingV01.getTargetRewardRate(bundle_nft) == bundle_rate_zero


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
    bundle_lifetime = 14 * 24 * 3600,
    bundle_id = 1,
    is_first_bundle = True
) -> int:
    # setup attributes
    chain_id = chainRegistryV01.toChain(mockInstance.getChainId())
    instance_id = mockInstance.getInstanceId()
    riskpool_id = 1
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
    if is_first_bundle:
        tx_token = chainRegistryV01.registerToken(
                chain_id,
                usd2,
                '',
                {'from': registryOwner})

    # register instance
    if is_first_bundle:
        tx_instance = chainRegistryV01.registerInstance(
            mockRegistry,
            'mockRegistry TEST',
            '',
            {'from': registryOwner})

    # register riskpool
    if is_first_bundle:
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
