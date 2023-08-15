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

from scripts.util import (
    contract_from_address,
    unix_timestamp
)

# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_staking_facade(
    mockInstance,
    instanceOperator,
    stakingProxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    stakingV01Implementation: StakingV01,
    stakingV01: StakingV01,
    stakingOwner: Account,
    dip: interface.IERC20Metadata,
    usd2: USD2,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account
):
    pa = stakingProxyAdmin
    pao = proxyAdminOwner
    si = stakingV01Implementation
    s = stakingV01
    so = stakingOwner
    r = chainRegistryV01
    ro = registryOwner
    o = theOutsider

    fro = {'from': registryOwner}
    fso = {'from': stakingOwner}
    fio = {'from': instanceOperator}

    s_facade = contract_from_address(interface.IStakingFacade, s)

    # check owner
    assert s_facade.owner() == so
    assert s_facade.owner() == s.owner()

    # check registry
    assert s_facade.getRegistry() == r
    assert s_facade.getRegistry() == s.getRegistry()

    # check staking wallet
    staking_wallet = s
    assert s_facade.getStakingWallet() == staking_wallet
    assert s_facade.getStakingWallet() == s.getStakingWallet()

    s.setStakingWallet(theOutsider, fso)
    assert s_facade.getStakingWallet() == theOutsider
    assert s_facade.getStakingWallet() == s.getStakingWallet()

    # check dip
    assert s_facade.getDip() == dip
    assert s_facade.getDip() == s.getDip()

    # check reward rate (and toRate/rateDecimals)
    s_facade.rateDecimals() == 18
    s_facade.rateDecimals() == s.rateDecimals()

    assert s_facade.maxRewardRate()/10**s_facade.rateDecimals() == 0.333
    assert s_facade.maxRewardRate() == s.maxRewardRate()

    s.setRewardRate(s.toRate(123, -3), fso)
    assert s_facade.rewardRate()/10**s_facade.rateDecimals() == 0.123
    assert s_facade.rewardRate() == s.rewardRate()

    # check staking rate (and toChain)
    chain_id = s.toChain(web3.chain_id)
    usd2_rate = s.toRate(5, -2)
    r.registerToken(chain_id, usd2, 'usd2', fro)
    s.setStakingRate(chain_id, usd2, usd2_rate, fso)

    assert s_facade.toChain(web3.chain_id) == chain_id
    assert s_facade.stakingRate(chain_id, usd2) == usd2_rate

    # check capitalSupport
    instance_id = mockInstance.getInstanceId()
    riskpool_id = 7
    type_riskpool = 2 # see IInstanceServiceFacade
    state_active = 3 # see IInstanceServiceFacade

    bundle_id = 42
    bundle_state_active = 0 # enum BundleState { Active, Locked, Closed, Burned }
    bundle_funding = 1234 * 10 ** usd2.decimals()
    bundle_name = 'my bundle'
    bundle_expiry = unix_timestamp() + 14 * 24 * 3600

    mockInstance.setComponentInfo(riskpool_id, type_riskpool, state_active, usd2)
    mockInstance.setBundleInfo(bundle_id, riskpool_id, bundle_state_active, bundle_funding)

    r.registerInstance(mockInstance.getRegistry(), 'mock instance', '', fro)
    r.registerComponent(instance_id, riskpool_id, '', fro)
    r.registerBundle(instance_id, riskpool_id, bundle_id, bundle_name, bundle_expiry, fro)

    bundle_nft = r.getBundleNftId(instance_id, bundle_id)

    # and now the check
    assert s_facade.capitalSupport(bundle_nft) == 0
    assert s_facade.capitalSupport(bundle_nft) == s.capitalSupport(bundle_nft)

    # stake some and check again
    dip_amount = 10000 * 10**dip.decimals()

    dip.approve(s, dip_amount, fio)
    s.createStake(bundle_nft, dip_amount, fio)

    capital_support_expected = int(0.05 * 10000 * 10**usd2.decimals())
    assert s_facade.capitalSupport(bundle_nft) == capital_support_expected
    assert s_facade.capitalSupport(bundle_nft) == s.capitalSupport(bundle_nft)

    assert s_facade.stakeBalance() == dip_amount
    assert s_facade.stakeBalance() == s.stakeBalance()

    # check implementsIStaking
    assert s_facade.implementsIStaking() is True
    assert s_facade.implementsIStaking() == s.implementsIStaking()

    # check version(parts)
    assert s_facade.version() == 1 * 2**32 + 1 * 2**16 + 1 * 2**0
    assert s_facade.version() == s.version()

    assert s_facade.versionParts() == (1, 1, 1)
    assert s_facade.versionParts() == s.versionParts()
