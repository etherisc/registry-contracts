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

# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_reward_rate(
    stakingV01: StakingV01,
    stakingOwner: Account,
    theOutsider: Account
):
    s = stakingV01

    rr00 = stakingV01.toRate(0, 0)
    rr10 = stakingV01.toRate(1, -1)
    rr30 = stakingV01.toRate(3, -1)
    rr40 = stakingV01.toRate(4, -1)

    assert s.rewardRate() == rr00

    # check restriction to owner
    with brownie.reverts('Ownable: caller is not the owner'):
        s.setRewardRate(rr40, {'from': theOutsider})

    # check max reward rate restriction 
    with brownie.reverts('ERROR:STK-070:REWARD_EXCEEDS_MAX_VALUE'):
        s.setRewardRate(rr40, {'from': stakingOwner})

    # check happy path
    s.setRewardRate(rr30, {'from': stakingOwner})
    assert s.rewardRate() == rr30
    assert s.rewardRate() / 10 ** s.rateDecimals() == 0.3

    # check setting back to 0 and to some other value > 0
    s.setRewardRate(rr00, {'from': stakingOwner})
    assert s.rewardRate() == rr00
    assert s.rewardRate() == 0

    s.setRewardRate(rr10, {'from': stakingOwner})
    assert s.rewardRate() == rr10
    assert s.rewardRate() / 10 ** s.rateDecimals() == 0.1


def test_reward_reserves(
    stakingV01: StakingV01,
    stakingOwner: Account,
    dip: interface.IERC20Metadata,
    instanceOperator: Account,
    theOutsider: Account,
):
    s = stakingV01
    assert s.rewardReserves() == 0

    # attempt to increase by 0
    with brownie.reverts('ERROR:STK-080:DIP_AMOUNT_ZERO'):
        s.refillRewardReserves(0, {'from': theOutsider })

    # attempt to increase without allownace
    reserves  = 10000 * 10 ** dip.decimals()
    with brownie.reverts('ERC20: insufficient allowance'):
        s.refillRewardReserves(reserves, {'from': theOutsider })

    dip.approve(s, reserves, {'from': theOutsider })

    # attempt to increase without balance
    with brownie.reverts('ERC20: transfer amount exceeds balance'):
        s.refillRewardReserves(reserves, {'from': theOutsider })

    dip.transfer(theOutsider, reserves, {'from': instanceOperator })
    assert s.rewardReserves() == 0
    assert dip.balanceOf(theOutsider) == reserves
    assert dip.balanceOf(stakingOwner) == 0

    # check increasing reserves
    s.refillRewardReserves(reserves, {'from': theOutsider })
    assert s.rewardReserves() == reserves
    assert dip.balanceOf(theOutsider) == 0
    assert dip.balanceOf(stakingOwner) == 0

    # attempt withdrawal of 0 as the outsider
    with brownie.reverts('Ownable: caller is not the owner'):
        s.withdrawRewardReserves(0, {'from': theOutsider})

    # attempt withdrawal of 0 as staking owner
    with brownie.reverts('ERROR:STK-090:DIP_AMOUNT_ZERO'):
        s.withdrawRewardReserves(0, {'from': stakingOwner})

    # attempt withdrawal of more than availables reserves
    with brownie.reverts('ERROR:STK-091:DIP_RESERVES_INSUFFICIENT'):
        s.withdrawRewardReserves(reserves + 1, {'from': stakingOwner})

    # withdrwal of 20% of reserves
    partial_reserves = 0.2 * reserves
    s.withdrawRewardReserves(partial_reserves, {'from': stakingOwner})
    assert s.rewardReserves() == reserves - partial_reserves
    assert dip.balanceOf(theOutsider) == 0
    assert dip.balanceOf(stakingOwner) == partial_reserves

    # withdrwal of remaining reserves
    remaining_reserves = s.rewardReserves()
    s.withdrawRewardReserves(remaining_reserves, {'from': stakingOwner})
    assert s.rewardReserves() == 0
    assert dip.balanceOf(theOutsider) == 0
    assert dip.balanceOf(stakingOwner) == partial_reserves + remaining_reserves
    assert dip.balanceOf(stakingOwner) == reserves


def test_staking_rate(
    stakingV01: StakingV01,
    stakingOwner: Account,
    registryOwner: Account,
    usd1: USD1,
    theOutsider: Account
):
    s = stakingV01
    r = contract_from_address(ChainRegistryV01, s.getRegistry())
    chain = r.toChain(web3.chain_id)

    sr00 = stakingV01.toRate(0, 0)
    sr01 = stakingV01.toRate(1, -2)
    sr10 = stakingV01.toRate(1, -1)

    assert s.stakingRate(chain, usd1) == sr00

    # check restriction to owner
    with brownie.reverts('Ownable: caller is not the owner'):
        s.setStakingRate(chain, usd1, sr00, {'from': theOutsider})

    # check restriction to registered tokens
    with brownie.reverts('ERROR:STK-005:NOT_REGISTERED'):
        s.setStakingRate(chain, usd1, sr00, {'from': stakingOwner})

    r.registerToken(chain, usd1, {'from': registryOwner})

    # check restriction to staking rates > 0
    with brownie.reverts('ERROR:STK-060:STAKING_RATE_ZERO'):
        s.setStakingRate(chain, usd1, sr00, {'from': stakingOwner})

    # check happy case
    s.setStakingRate(chain, usd1, sr01, {'from': stakingOwner})
    assert s.stakingRate(chain, usd1) == sr01
    assert s.stakingRate(chain, usd1) / 10 ** s.rateDecimals() == 0.01

    # check chaning staking rate is possible
    s.setStakingRate(chain, usd1, sr10, {'from': stakingOwner})
    assert s.stakingRate(chain, usd1) == sr10
    assert s.stakingRate(chain, usd1) / 10 ** s.rateDecimals() == 0.1


def test_is_staking_supported(
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

    (
        instance_id,
        riskpool_id,
        bundle_id,
        token
    ) = chainRegistryV01.decodeBundleData(bundle_nft)
    
    instance_service = contract_from_address(
        interface.IInstanceServiceFacade, 
        chainRegistryV01.getInstanceServiceFacade(instance_id))
    
    bundle_state_active = 0 # enum BundleState { Active, Locked, Closed, Burned }
    bundle_state_locked = 1
    bundle_state_closed = 2
    bundle_state_burned = 3

    bundle = instance_service.getBundle(bundle_id).dict()
    assert bundle['state'] == bundle_state_active

    # check that staking for active bundle is possible
    assert stakingV01.isStakingSupported(bundle_nft) is True

    # cycle through other bundle stakes and check that staking is not supported
    bundle_funding = 1234 * 10 ** usd2.decimals()
    mockInstance.setBundleInfo(bundle_id, riskpool_id, bundle_state_locked, bundle_funding)
    assert instance_service.getBundle(bundle_id).dict()['state'] == bundle_state_locked
    assert stakingV01.isStakingSupported(bundle_nft) is False

    mockInstance.setBundleInfo(bundle_id, riskpool_id, bundle_state_closed, bundle_funding)
    assert instance_service.getBundle(bundle_id).dict()['state'] == bundle_state_closed
    assert stakingV01.isStakingSupported(bundle_nft) is False

    mockInstance.setBundleInfo(bundle_id, riskpool_id, bundle_state_burned, bundle_funding)
    assert instance_service.getBundle(bundle_id).dict()['state'] == bundle_state_burned
    assert stakingV01.isStakingSupported(bundle_nft) is False

    # reset to active and check staking is again possible
    mockInstance.setBundleInfo(bundle_id, riskpool_id, bundle_state_active, bundle_funding)
    assert instance_service.getBundle(bundle_id).dict()['state'] == bundle_state_active
    assert stakingV01.isStakingSupported(bundle_nft) is True

    # wait long enough and check that staking is no longer possible
    chain.sleep(stakingV01.BUNDLE_LIFETIME_DEFAULT() - 10)
    chain.mine(1)

    # staking should still be good
    assert stakingV01.isStakingSupported(bundle_nft) is True

    chain.sleep(20)
    chain.mine(1)

    # beyond expiry, staking no longer possible
    assert stakingV01.isStakingSupported(bundle_nft) is False


def test_stake_bundle_happy_path(
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

    # check if in principle staking is possible
    assert stakingV01.isStakingSupportedForType(chainRegistryV01.BUNDLE()) is True
    assert stakingV01.isStakingSupported(bundle_nft) is True

    # check no staking for this bundle and user so far
    assert stakingV01.hasInfo(bundle_nft, staker) is False

    # attempt to stake
    staking_amount = 5000 * 10 ** dip.decimals()
    prepare_staker(staker, staking_amount, dip, instanceOperator, stakingV01)

    # check balances before staking
    assert dip.balanceOf(staker) == staking_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()) == 0

    staking_tx = stakingV01.stake(
        bundle_nft,
        staking_amount,
        {'from': staker })

    # check balances after staking
    assert dip.balanceOf(staker) == 0
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
    assert 'LogStakingNewStakes' in staking_tx.events
    evt = staking_tx.events['LogStakingNewStakes']
    assert evt['target'] == bundle_nft
    assert evt['user'] == staker
    assert evt['id'] == nft_id

    # check nft info in registry
    assert chainRegistryV01.ownerOf(nft_id) == staker

    state_approved = 2 # ObjectState { Undefined, Proposed, Approved, ...}
    info = chainRegistryV01.getNftInfo(nft_id).dict()
    assert info['id'] == nft_id
    assert info['t'] == chainRegistryV01.STAKE()
    assert info['state'] == state_approved
    (target_id, target_type) = chainRegistryV01.decodeStakeData(nft_id)
    assert target_id == bundle_nft
    assert target_type == chainRegistryV01.BUNDLE()

    # check staking info for nft
    assert stakingV01.hasInfo(bundle_nft, staker) is True
    info = stakingV01.getInfo(bundle_nft, staker).dict()
    block_timestamp = web3.eth.getBlock(web3.eth.block_number)['timestamp']
    assert info['id'] == nft_id
    assert info['target'] == bundle_nft
    assert info['stakeBalance'] == staking_amount
    assert info['rewardBalance'] == 0
    assert info['createdAt'] == block_timestamp
    assert info['updatedAt'] == block_timestamp


def test_increase_stakes(
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

    # prepare inital stakes
    staking_amount = 5000 * 10 ** dip.decimals()
    prepare_staker(staker, staking_amount, dip, instanceOperator, stakingV01)

    staking_tx = stakingV01.stake(
        bundle_nft,
        staking_amount,
        {'from': staker })

    assert 'LogStakingNewStakes' in staking_tx.events
    assert 'LogStakingStaked' in staking_tx.events

    # prepare increasing stakes
    additional_amount = 42 * 10 ** dip.decimals()
    prepare_staker(staker, additional_amount, dip, instanceOperator, stakingV01)

    # check balances before staking
    assert dip.balanceOf(staker) == additional_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()) == staking_amount

    # increase stakes
    increase_tx = stakingV01.stake(
        bundle_nft,
        additional_amount,
        {'from': staker })

    # check balances after staking
    assert dip.balanceOf(staker) == 0
    assert dip.balanceOf(stakingV01.getStakingWallet()) == staking_amount + additional_amount

    assert 'LogStakingNewStakes' not in increase_tx.events
    assert 'LogStakingStaked' in increase_tx.events

    evt = increase_tx.events['LogStakingStaked']
    assert evt['target'] == bundle_nft
    assert evt['user'] == staker
    assert evt['amount'] == additional_amount
    assert evt['newBalance'] == staking_amount + additional_amount


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
    riskpool_id = 1
    bundle_id = 1
    bundle_name = 'my test bundle'
    bundle_funding = 10000 * 10 ** usd2.decimals()
    bundle_expiry_at = unix_timestamp() + 14 * 24 * 3600

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
            {'from': registryOwner})

    # register instance
    tx_instance = chainRegistryV01.registerInstance(
        mockRegistry,
        "mockRegistry TEST",
        {'from': registryOwner})

    # register riskpool
    tx_riskpool = chainRegistryV01.registerComponent(
        instance_id,
        riskpool_id,
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
