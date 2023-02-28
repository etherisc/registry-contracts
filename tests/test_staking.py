import pytest
import brownie

from brownie.network.account import Account

from brownie import (
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
from scripts.util import contract_from_address

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
