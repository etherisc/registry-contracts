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
    ChainNft,
    StakingV01,
    StakingV02,
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


def test_stake_and_unstake_simple(
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
        {'from': staker})

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
        stakingV01.unstake(nft_id, 1, {'from': staker})

    # close bundle
    mockInstance.setBundleInfo(
        BUNDLE_ID,
        RISKPOOL_ID,
        BUNDLE_STATE_CLOSED,
        BUNDLE_FUNDING * 10 ** dip.decimals())

    assert stakingV01.isUnstakingSupported(bundle_nft) is True

    unstake_amount = int(staking_amount / 3)
    unstake_tx = stakingV01.unstake(nft_id, unstake_amount, {'from': staker})

    # check balances after unstaking
    assert dip.balanceOf(staker) == unstake_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()
                         ) == staking_amount - unstake_amount

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


def test_stake_transfer_and_unstake(
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
    staker2: Account,
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
        {'from': staker})

    # check balances after staking
    assert dip.balanceOf(staker) == 0
    assert dip.balanceOf(stakingV01.getStakingWallet()) == staking_amount

    # get stake nft id
    created_at = web3.eth.getBlock(web3.eth.block_number)['timestamp']
    assert 'LogStakingStaked' in staking_tx.events
    evt = staking_tx.events['LogStakingStaked']
    nft_id = evt['id']

    # check ownership directly on registry
    assert chainRegistryV01.ownerOf(nft_id) == staker
    assert chainRegistryV01.ownerOf(nft_id) != staker2

    nft = contract_from_address(ChainNft, chainRegistryV01.getNft())
    # ensure staker2 can not just take stake nft over
    with brownie.reverts('ERC721: caller is not token owner or approved'):
        nft.transferFrom(staker, staker2, nft_id, {'from': staker2})

    # ordinary nft transfer
    transfer_tx = nft.transferFrom(staker, staker2, nft_id, {'from': staker})

    assert 'Transfer' in transfer_tx.events
    evt = dict(transfer_tx.events['Transfer'])
    assert evt['from'] == staker
    assert evt['to'] == staker2
    assert evt['tokenId'] == nft_id

    # check ownership directly on registry
    assert chainRegistryV01.ownerOf(nft_id) == staker2
    assert chainRegistryV01.ownerOf(nft_id) != staker

    # close bundle
    mockInstance.setBundleInfo(
        BUNDLE_ID,
        RISKPOOL_ID,
        BUNDLE_STATE_CLOSED,
        BUNDLE_FUNDING * 10 ** dip.decimals())

    assert stakingV01.isUnstakingSupported(bundle_nft) is True

    unstake_amount = int(staking_amount / 3)

    # attempt by old nft owner to unstake
    with brownie.reverts('ERROR:STK-010:USER_NOT_OWNER'):
        stakingV01.unstake(nft_id, unstake_amount, {'from': staker})

    # check that new nft owner can unstake
    unstake_tx = stakingV01.unstake(nft_id, unstake_amount, {'from': staker2})

    # check balances after unstaking
    assert dip.balanceOf(staker) == 0
    assert dip.balanceOf(staker2) == unstake_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()
                         ) == staking_amount - unstake_amount

    assert 'LogStakingUnstaked' in unstake_tx.events
    evt = dict(unstake_tx.events['LogStakingUnstaked'])
    assert evt['id'] == nft_id
    assert evt['target'] == bundle_nft
    assert evt['user'] == staker2
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


def test_stake_and_claim_rewards(
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
        theOutsider)

    assert bundle_nft > 0

    # prepare reward rate: 20.0% apr
    reward_rate = stakingV01.toRate(20, -2)
    stakingV01.setRewardRate(reward_rate, {'from': stakingOwner})
    assert stakingV01.rewardRate() == reward_rate

    # add dips to allow for reward claims
    reward_reserves = 10000 * 10 ** dip.decimals()
    dip.approve(stakingV01, reward_reserves, {'from': instanceOperator})
    stakingV01.refillRewardReserves(
        reward_reserves, {'from': instanceOperator})
    assert stakingV01.rewardReserves() == reward_reserves

    # prepare staker
    staking_amount = 100000 * 10 ** dip.decimals()
    prepare_staker(staker, staking_amount, dip, instanceOperator, stakingV01)

    staking_tx = stakingV01.createStake(
        bundle_nft,
        staking_amount,
        {'from': staker})

    # get stake nft id
    created_at = web3.eth.getBlock(web3.eth.block_number)['timestamp']
    assert 'LogStakingStaked' in staking_tx.events
    evt = staking_tx.events['LogStakingStaked']
    nft_id = evt['id']

    quarter_year = int(stakingV01.YEAR_DURATION() / 4)
    chain.sleep(quarter_year)
    chain.mine(1)

    # close bundle
    mockInstance.setBundleInfo(
        BUNDLE_ID,
        RISKPOOL_ID,
        BUNDLE_STATE_CLOSED,
        BUNDLE_FUNDING * 10 ** dip.decimals())

    # check that not anybody can execute claimRewards
    with brownie.reverts('ERROR:STK-010:USER_NOT_OWNER'):
        stakingV01.claimRewards(nft_id, {'from': theOutsider})

    dip_balance_before = dip.balanceOf(staker)
    dip_reserves_before = dip.balanceOf(stakingV01.getStakingWallet())

    stake_info = stakingV01.getInfo(nft_id)
    rewards_increment = stakingV01.calculateRewardsIncrement(stake_info)

    # check that actual owner can claim
    claimed_tx = stakingV01.claimRewards(nft_id, {'from': staker})
    claimed_at = web3.eth.getBlock(web3.eth.block_number)['timestamp']

    dip_balance_after = dip.balanceOf(staker)
    dip_reserves_after = dip.balanceOf(stakingV01.getStakingWallet())

    quarter_year_rewards_amount = stakingV01.calculateRewards(
        staking_amount, claimed_at - created_at)

    assert delta_is_tiny(quarter_year_rewards_amount, rewards_increment)

    # check log entries
    assert 'LogStakingRewardsUpdated' in claimed_tx.events
    evt_update = dict(claimed_tx.events['LogStakingRewardsUpdated'])
    assert evt_update['id'] == nft_id
    assert evt_update['amount'] == evt_update['newBalance']
    assert delta_is_tiny(evt_update['amount'], quarter_year_rewards_amount)

    assert 'LogStakingRewardsClaimed' in claimed_tx.events
    evt_claimed = dict(claimed_tx.events['LogStakingRewardsClaimed'])
    assert evt_claimed['id'] == evt_update['id']
    assert evt_claimed['amount'] == evt_update['amount']
    assert evt_claimed['newBalance'] == 0

    assert 'Transfer' in claimed_tx.events
    evt_transfer = dict(claimed_tx.events['Transfer'])
    assert evt_transfer['from'] == stakingV01.getStakingWallet()
    assert evt_transfer['to'] == staker
    assert evt_transfer['value'] == evt_claimed['amount']

    # check dip balances
    rewards = evt_claimed['amount']
    assert dip_balance_before + rewards == dip_balance_after
    assert dip_reserves_before - rewards == dip_reserves_after


def test_stake_unstake_and_claim_rewards(
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
        {'from': staker})

    # get stake nft id
    created_at = web3.eth.getBlock(web3.eth.block_number)['timestamp']
    assert 'LogStakingStaked' in staking_tx.events
    evt = staking_tx.events['LogStakingStaked']
    nft_id = evt['id']

    quarter_year = int(stakingV01.YEAR_DURATION() / 4)
    chain.sleep(quarter_year)
    chain.mine(1)

    # close bundle
    mockInstance.setBundleInfo(
        BUNDLE_ID,
        RISKPOOL_ID,
        BUNDLE_STATE_CLOSED,
        BUNDLE_FUNDING * 10 ** dip.decimals())

    # unstake 1
    unstake_tx = stakingV01.unstake(nft_id, 1, {'from': staker})
    unstaked_at = web3.eth.getBlock(web3.eth.block_number)['timestamp']

    quarter_year_rewards_amount = stakingV01.calculateRewards(
        staking_amount, unstaked_at - created_at)

    assert 'LogStakingRewardsUpdated' in unstake_tx.events
    evt = dict(unstake_tx.events['LogStakingRewardsUpdated'])
    assert evt['id'] == nft_id
    assert delta_is_tiny(evt['amount'], quarter_year_rewards_amount)
    assert evt['amount'] == evt['newBalance']

    info = stakingV01.getInfo(nft_id).dict()
    assert info['rewardBalance'] == evt['newBalance']

    # check that not anybody can execute claimRewards
    with brownie.reverts('ERROR:STK-010:USER_NOT_OWNER'):
        stakingV01.claimRewards(nft_id, {'from': theOutsider})

    # check initial reward balance/reserves
    assert delta_is_tiny(stakingV01.rewardBalance(), quarter_year_rewards_amount)
    assert stakingV01.rewardReserves() == 0

    # check that nft owner can claim rewards
    claim_tx = stakingV01.claimRewards(nft_id, {'from': staker})

    # check no rewards have been payed (as reward reserves are empty)
    assert 'LogStakingRewardsClaimed' in claim_tx.events
    evt = dict(claim_tx.events['LogStakingRewardsClaimed'])
    assert evt['id'] == nft_id
    assert evt['amount'] == 0
    assert evt['newBalance'] == stakingV01.rewardBalance()

    # add some reward reserves and try again
    reward_amount = info['rewardBalance']
    reserves_amount = 10000 * 10 ** dip.decimals()
    dip.approve(stakingV01.getStakingWallet(),
                reserves_amount, {'from': instanceOperator})
    reserve_tx = stakingV01.refillRewardReserves(
        reserves_amount, {'from': instanceOperator})

    assert stakingV01.rewardReserves() == reserves_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()) == staking_amount - 1 + reserves_amount

    # check again that nft owner can claim rewards
    info_before = stakingV01.getInfo(nft_id).dict()
    claim_tx2 = stakingV01.claimRewards(nft_id, {'from': staker})
    rewards_claimed = claim_tx2.events['LogStakingRewardsClaimed']['amount']

    # balance check
    wallet_balance = dip.balanceOf(stakingV01.getStakingWallet())
    wallet_balance_expected = staking_amount - 1 + reserves_amount - rewards_claimed
    assert wallet_balance == wallet_balance_expected
    assert delta_is_tiny(reward_amount, rewards_claimed)
    assert dip.balanceOf(staker) == 1 + rewards_claimed

    # check rewards have now been payed
    assert 'LogStakingRewardsClaimed' in claim_tx2.events
    evt = dict(claim_tx2.events['LogStakingRewardsClaimed'])
    assert evt['id'] == nft_id
    assert evt['amount'] == rewards_claimed
    assert evt['newBalance'] == 0

    # check staking info for nft after unstaking
    info_after = stakingV01.getInfo(nft_id).dict()
    assert info_after['rewardBalance'] == 0
    assert info_after['id'] == info_before['id']
    assert info_after['target'] == info_before['target']
    assert info_after['stakeBalance'] == info_before['stakeBalance']
    assert info_after['createdAt'] == info_before['createdAt']
    assert info_after['updatedAt'] >= info_before['updatedAt']

    # wait a bit (to get some additional rewards)
    chain.sleep(14 * 24 * 3600)
    chain.mine(1)

    unstake_and_claim_tx = stakingV01.unstakeAndClaimRewards(nft_id, {'from': staker})

    evts = unstake_and_claim_tx.events
    assert 'LogStakingRewardsUpdated' in evts
    assert 'LogStakingUnstaked' in evts
    assert 'LogStakingRewardsClaimed' in evts

    assert evts['LogStakingRewardsUpdated']['id'] == nft_id
    assert evts['LogStakingRewardsUpdated']['amount'] > 0
    assert evts['LogStakingRewardsUpdated']['amount'] == evts['LogStakingRewardsUpdated']['newBalance']

    assert evts['LogStakingUnstaked']['id'] == nft_id
    assert evts['LogStakingUnstaked']['amount'] == staking_amount - 1
    assert evts['LogStakingUnstaked']['newBalance'] == 0

    assert evts['LogStakingRewardsClaimed']['id'] == nft_id
    assert evts['LogStakingRewardsClaimed']['amount'] == evts['LogStakingRewardsUpdated']['newBalance']
    assert evts['LogStakingRewardsClaimed']['newBalance'] == 0

    # final balance check
    assert dip.balanceOf(stakingV01.getStakingWallet()) == reserves_amount - \
        rewards_claimed - evts['LogStakingRewardsClaimed']['amount']
    assert dip.balanceOf(staker) == staking_amount + \
        rewards_claimed + evts['LogStakingRewardsClaimed']['amount']


def delta_is_tiny(a, b, epsilon=10 ** -10):
    return abs(1 - (a / b)) < 10 ** epsilon


def prepare_staker(
    staker,
    staking_amount,
    dip,
    instanceOperator,
    stakingV01
):
    dip.transfer(staker, staking_amount, {'from': instanceOperator})
    dip.approve(stakingV01.getStakingWallet(),
                staking_amount, {'from': staker})


def create_mock_bundle_setup(
    mockInstance: MockInstance,
    mockRegistry: MockInstanceRegistry,
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

    # enum BundleState { Active, Locked, Closed, Burned }
    bundle_state_active = 0
    mockInstance.setBundleInfo(
        BUNDLE_ID,
        RISKPOOL_ID,
        BUNDLE_STATE_ACTIVE,
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
        RISKPOOL_ID,
        '',
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
