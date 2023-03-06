import brownie
import pytest

from brownie.network.account import Account
from brownie import (
    exceptions,
    web3,
    ChainRegistryV01,
    StakingV01,
    DIP,
    USD1,
    USD3
)

# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_staking_rate_happy_case(
    registryOwner: Account,
    stakingOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    stakingV01: StakingV01,
    dip: DIP,
    usd1: USD1,
    usd3: USD3
):
    staking = stakingV01
    chain = chainRegistryV01.toChain(web3.chain_id)

    exp = 6
    staking_rate_f = 0.123456 # 1 dip unlocks 12.3456 cents (usd1)
    staking_rate_i = staking_rate_f * 10 ** exp
    staking_rate = staking.toRate(staking_rate_i, -exp)

    rate = staking_rate / 10 ** staking.rateDecimals()
    assert rate == staking_rate_f

    # register token and get initial rate
    chainRegistryV01.registerToken(chain, usd1.address, {'from': registryOwner})
    staking_rate_initial = staking.stakingRate(chain, usd1)

    assert staking.stakingRate(chain, usd1) == 0
    assert staking.stakingRate(chain, usd3) == 0

    # set staking rate for usd1
    tx = staking.setStakingRate(
        chain,
        usd1,
        staking_rate,
        {'from': stakingOwner})

    assert staking.stakingRate(chain, usd1) == staking_rate
    assert staking.stakingRate(chain, usd3) == 0

    staking_rate_now = staking.stakingRate(chain, usd1)

    # check event
    assert 'LogStakingStakingRateSet' in tx.events
    assert tx.events['LogStakingStakingRateSet']['token'] == usd1
    assert tx.events['LogStakingStakingRateSet']['chain'] == chain
    assert tx.events['LogStakingStakingRateSet']['oldStakingRate'] == staking_rate_initial
    assert tx.events['LogStakingStakingRateSet']['newStakingRate'] == staking_rate_now

    # set staking rate for usd3
    chainRegistryV01.registerToken(chain, usd3, {'from': registryOwner})
    staking.setStakingRate(
        chain,
        usd3,
        staking_rate,
        {'from': stakingOwner})

    # check staking rates
    usd1_staking_rate = staking.stakingRate(chain, usd1)
    usd3_staking_rate = staking.stakingRate(chain, usd3)

    assert usd1_staking_rate == staking_rate
    assert usd3_staking_rate == staking_rate

    one_dip = 10**dip.decimals()
    one_usd1 = 10**usd1.decimals()
    one_usd3 = 10**usd3.decimals()

    assert one_usd1 != one_usd3

    ## check dip staking -> supported token amount
    dip_amount = 10 * one_dip

    usd1_amount = staking.calculateCapitalSupport(chain, usd1, dip_amount)
    usd3_amount = staking.calculateCapitalSupport(chain, usd3, dip_amount)

    # check resulting supported amounts
    usd1_amount_expected = round(10 * staking_rate_f * 10 ** usd1.decimals())
    usd3_amount_expected = round(10 * staking_rate_f * 10 ** usd3.decimals())

    assert usd1_amount == usd1_amount_expected
    assert usd3_amount == usd3_amount_expected


def test_conversion_calculation_usd1(
    registryOwner,
    stakingOwner,
    chainRegistryV01: ChainRegistryV01,
    stakingV01: StakingV01,
    usd1: USD1
):
    staking = stakingV01
    chain = chainRegistryV01.toChain(web3.chain_id)

    exp = 6
    staking_rate_f = 0.123456 # 1 dip unlocks 12.3456 cents (usd1)
    staking_rate_i = staking_rate_f * 10 ** exp
    staking_rate = staking.toRate(staking_rate_i, -exp)

    # set staking rate for usd1
    chainRegistryV01.registerToken(chain, usd1.address, {'from': registryOwner})
    staking.setStakingRate(
        chain,
        usd1,
        staking_rate,
        {'from': stakingOwner})

    # calculate dips needed to support 25 usd1
    mult_usd1 = 10**usd1.decimals()
    target_usd1 = 25
    target_amount = target_usd1 * mult_usd1
    required_dip = staking.calculateRequiredStaking(
        chain,
        usd1,
        target_amount)

    assert required_dip > 0

    supported_usd1 = staking.calculateCapitalSupport(
        chain,
        usd1,
        required_dip)

    print('staking_rate {} target_usd1 {} required_dip {} supported_usd1 {}'.format(
        staking_rate,
        target_usd1,
        required_dip,
        supported_usd1))

    assert abs(target_amount - supported_usd1) <= 1


def test_conversion_calculation_usd3(
    registryOwner,
    stakingOwner,
    chainRegistryV01: ChainRegistryV01,
    stakingV01: StakingV01,
    usd3: USD3
):
    staking = stakingV01
    chain = chainRegistryV01.toChain(web3.chain_id)

    exp = 6
    staking_rate_f = 0.123456 # 1 dip unlocks 12.3456 cents (usd1)
    staking_rate_i = staking_rate_f * 10 ** exp
    staking_rate = staking.toRate(staking_rate_i, -exp)

    # set staking rate for usd1
    chainRegistryV01.registerToken(chain, usd3, {'from': registryOwner})
    staking.setStakingRate(
        chain,
        usd3,
        staking_rate,
        {'from': stakingOwner})

    # calculate dips needed to support 25 usd1
    mult_usd3 = 10**usd3.decimals()
    target_usd3 = 39
    target_amount = target_usd3 * mult_usd3
    required_dip = staking.calculateRequiredStaking(
        chain,
        usd3,
        target_amount)

    assert required_dip > 0

    supported_usd3 = staking.calculateCapitalSupport(
        chain,
        usd3,
        required_dip)

    print('staking_rate {} target_usd3 {} required_dip {} supported_usd3 {}'.format(
        staking_rate,
        target_usd3,
        required_dip,
        supported_usd3))

    assert abs(target_amount - supported_usd3) <= 1


def test_staking_rate_failure_modes(
    registryOwner,
    stakingOwner,    
    instanceOperator,
    chainRegistryV01: ChainRegistryV01,
    stakingV01: StakingV01,
    usd1: USD1
):
    staking = stakingV01
    chain = chainRegistryV01.toChain(web3.chain_id)

    # attempt to get staking rate for non-registered token
    assert staking.stakingRate(chain, usd1) == 0

    exp = 6
    staking_rate_f = 0.123456 # 1 dip unlocks 12.3456 cents (usd1)
    staking_rate_i = staking_rate_f * 10 ** exp
    staking_rate = staking.toRate(staking_rate_i, -exp)

    # attempt to set rate as non-staking-owner
    with brownie.reverts('Ownable: caller is not the owner'):
        staking.setStakingRate(
            chain,
            usd1,
            staking_rate,
            {'from': registryOwner})

    # attempt to set rate for non-registered token
    with brownie.reverts('ERROR:STK-005:NOT_REGISTERED'):
        staking.setStakingRate(
            chain,
            usd1,
            staking_rate,
            {'from': stakingOwner})

    chainRegistryV01.registerToken(chain, usd1, {'from': registryOwner})

    # attempt to set zero rate
    staking_rate_zero = 0

    with brownie.reverts('ERROR:STK-110:STAKING_RATE_ZERO'):
        staking.setStakingRate(
            chain,
            usd1,
            staking_rate_zero,
            {'from': stakingOwner})


def test_calculating_failure_modes(
    chainRegistryV01: ChainRegistryV01,
    stakingV01: StakingV01,
    stakingOwner,    
    usd1: USD1,
    dip: DIP
):
    staking = stakingV01
    chain = chainRegistryV01.toChain(web3.chain_id)

    # attempt to calculate staking for non-registered token
    one_usd1 = 10**usd1.decimals()
    one_dip = 10**dip.decimals()

    # attempt to caluclate without having set a staking rate
    with brownie.reverts("ERROR:STK-210:TOKEN_STAKING_RATE_NOT_SET"):
        staking.calculateRequiredStaking(chain, usd1, one_usd1)
    
    with brownie.reverts("ERROR:STK-211:TOKEN_STAKING_RATE_NOT_SET"):
        staking.calculateCapitalSupport(chain, usd1, one_dip)
