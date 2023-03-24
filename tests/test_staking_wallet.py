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
    OwnableProxyAdmin,
    ChainRegistryV01,
    ChainNft,
    StakingV01,
)

from scripts.const import ZERO_ADDRESS
from scripts.util import contract_from_address

# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_staking_wallet_rewards(
    instanceOperator: Account,
    stakingProxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    stakingV01Implementation: StakingV01,
    stakingV01: StakingV01,
    stakingOwner: Account,
    staker: Account,
    dip: interface.IERC20Metadata,
    usd1: USD1,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account
):
    fio = {'from': instanceOperator}
    fso = {'from': stakingOwner}

    # check initial setup wher contract is holding dips
    assert stakingV01.getStakingWallet() == stakingV01

    assert stakingV01.rewardReserves() == 0
    assert dip.balanceOf(stakingOwner) == 0

    # move 1'000'000 reward dip to staking
    reward_reserves = 1000000 * 10**dip.decimals()
    dip.approve(stakingV01, reward_reserves, fio)

    stakingV01.refillRewardReserves(reward_reserves, fio)

    assert stakingV01.rewardReserves() == reward_reserves
    assert dip.balanceOf(stakingOwner) == 0

    # pull out 10'000 dip from reserves
    partial_amount = 10000 * 10**dip.decimals()

    with brownie.reverts('Ownable: caller is not the owner'):
        stakingV01.withdrawRewardReserves(partial_amount, fio)

    stakingV01.withdrawRewardReserves(partial_amount, fso)

    assert stakingV01.rewardReserves() == reward_reserves - partial_amount
    assert dip.balanceOf(stakingOwner) == partial_amount

    # attempt to burn dips
    with brownie.reverts('ERROR:STK-030:STAKING_WALLET_ZERO'):
        stakingV01.setStakingWallet(ZERO_ADDRESS, fso)

    # attempt to re-set staking contract as staking wallet
    with brownie.reverts('ERROR:STK-031:STAKING_WALLET_SAME'):
        stakingV01.setStakingWallet(stakingV01, fso)

    # set external staking wallet (re-purpose staker)
    staking_wallet = staker
    assert staking_wallet != stakingV01
    assert dip.balanceOf(stakingV01) == reward_reserves - partial_amount
    assert dip.balanceOf(staking_wallet) == 0

    # attempt to set new wallet by non-owner
    with brownie.reverts('Ownable: caller is not the owner'):
        stakingV01.setStakingWallet(staking_wallet, fio)

    # check external wallet can be set
    tx = stakingV01.setStakingWallet(staking_wallet, fso)

    # check log entry
    assert 'LogStakingWalletChanged' in tx.events

    evt = dict(tx.events['LogStakingWalletChanged'])
    assert evt['user'] == stakingOwner
    assert evt['oldWallet'] == stakingV01
    assert evt['newWallet'] == staking_wallet

    # check new dip asset distribution
    assert stakingV01.rewardReserves() == reward_reserves - partial_amount
    assert dip.balanceOf(stakingV01) == 0
    assert dip.balanceOf(staking_wallet) == reward_reserves - partial_amount

    # attempt to further reduce reward reserves
    with brownie.reverts('ERROR:STK-301:DIP_ALLOWANCE_INSUFFICIENT'):
        stakingV01.withdrawRewardReserves(partial_amount, fso)
    
    # fix approval and check again
    dip.approve(stakingV01, partial_amount, {'from': staking_wallet})
    tx = stakingV01.withdrawRewardReserves(partial_amount, fso)

    # check new dip asset distribution
    assert stakingV01.rewardReserves() == reward_reserves - 2 * partial_amount
    assert dip.balanceOf(stakingV01) == 0
    assert dip.balanceOf(staking_wallet) == reward_reserves - 2 * partial_amount
    assert dip.balanceOf(stakingOwner) == 2 * partial_amount

    # this is prove that reward reserves can be properly accessed from external wallet

    # now move dip funds of external wallet back to staking contract
    tx = stakingV01.setStakingWallet(stakingV01, fso)

    # check log entry
    assert 'LogStakingWalletChanged' in tx.events

    evt = dict(tx.events['LogStakingWalletChanged'])
    assert evt['user'] == stakingOwner
    assert evt['oldWallet'] == staking_wallet
    assert evt['newWallet'] == stakingV01

    # attempt to access reward reserves
    with brownie.reverts('ERROR:STK-300:DIP_BALANCE_INSUFFICIENT'):
        stakingV01.withdrawRewardReserves(partial_amount, fso)
    
    # 'manually' move reward reserves back to staking contract
    reserve_balance = dip.balanceOf(staking_wallet) 
    dip.transfer(stakingV01, reserve_balance, {'from': staking_wallet})

    # check that access to reserve dipas works as expected
    stakingV01.withdrawRewardReserves(partial_amount, fso)

    # check new dip asset distribution
    assert stakingV01.rewardReserves() == reward_reserves - 3 * partial_amount
    assert dip.balanceOf(stakingV01) == reward_reserves - 3 * partial_amount
    assert dip.balanceOf(staking_wallet) == 0
    assert dip.balanceOf(stakingOwner) == 3 * partial_amount
