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


def test_staking_implementation(
    stakingV01Implementation: StakingV01,
    theOutsider,
):
    si = stakingV01Implementation

    # check current version
    assert si.version() == 1 * 2 ** 0

    (major, minor, patch) = si.versionParts()
    assert (major, minor, patch) == (0, 0, 1)

    # check version info after deploy
    assert si.versions() == 1
    assert si.getVersion(0) == si.version()

    with brownie.reverts('ERROR:VRN-010:INDEX_TOO_LARGE'):
        si.getVersion(1)

    info = si.getVersionInfo(si.getVersion(0)).dict()
    assert info['version'] == si.getVersion(0)
    assert info['implementation'] == si
    assert info['activatedBy'] == theOutsider


def test_staking_basics(
    stakingProxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    stakingV01Implementation: StakingV01,
    stakingV01: StakingV01,
    stakingOwner: Account,
    dip: interface.IERC20Metadata,
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

    # check accounts
    assert pa != si
    assert pa != ro
    assert pa != so
    assert pao != so
    assert pao != ro
    assert ro != o
    assert ro != so
    assert so != o

    # check ownerships
    assert pao == pa.owner()
    assert pao != si.owner()
    assert pao != r.owner()
    assert si.owner() == o
    assert si.owner() != s.owner()
    assert s.owner() == so

    # check proxy admin
    assert pa.getImplementation() == si

    # check current version
    assert s.version() == 1 * 2 ** 0

    (major, minor, patch) = si.versionParts()
    assert (major, minor, patch) == (0, 0, 1)

    # check version info after deploy
    assert s.versions() == 1
    assert s.getVersion(0) == si.version()

    with brownie.reverts('ERROR:VRN-010:INDEX_TOO_LARGE'):
        s.getVersion(1)

    info = s.getVersionInfo(si.getVersion(0)).dict()
    assert info['version'] == si.getVersion(0)
    assert info['implementation'] == si
    assert info['activatedBy'] == pao

    # check max reward rate
    maxRewardRateInt = s.maxRewardRate()
    maxRewardRate = maxRewardRateInt / 10 ** s.rateDecimals()
    assert maxRewardRate == 0.333

    # check dip contract
    dipContract = contract_from_address(interface.IERC20Metadata, s.getDip())
    assert dipContract == dip
    assert dipContract.symbol() == 'DIP'
    assert dipContract.decimals() == 18

    # check registry
    registry = contract_from_address(ChainRegistryV01, s.getRegistry())
    assert registry == r
    assert registry.version() == r.version()
    assert registry.owner() == r.owner()
    assert registry.name() == 'Dezentralized Insurance Protocol Registry'
    assert registry.symbol() == 'DIPR'

    # check reward rate and dip reserves
    assert s.rewardRate() == 0
    assert s.rewardReserves() == 0
