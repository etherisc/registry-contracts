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
    StakingV02,
)

from scripts.const import ZERO_ADDRESS
from scripts.util import contract_from_address

# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_staking_upgrade(
    stakingProxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    instanceOperator: Account,
    stakingV01ImplementationBeta: StakingV01,
    stakingV01Beta: StakingV01,
    stakingOwner: Account,
    dip: interface.IERC20Metadata,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account,
):

    # check proxy admin setup
    assert stakingProxyAdmin.getImplementation() == stakingV01ImplementationBeta
    assert stakingProxyAdmin.getProxy() == stakingV01Beta
    assert stakingProxyAdmin.owner() == proxyAdminOwner

    # check current version
    assert stakingV01Beta.version() == 1 * 2**32 + 0 * 2**16 + 0 * 2**0
    (major, minor, patch) = stakingV01Beta.versionParts()
    assert (major, minor, patch) == (1, 0, 0)

    # check version info after deploy
    assert stakingV01Beta.versions() == 1
    assert stakingV01Beta.getVersion(0) == stakingV01ImplementationBeta.version()

    # deploy upgraded implementation
    stakingImplementation = StakingV02.deploy({'from': theOutsider})
    assert stakingImplementation != stakingV01ImplementationBeta

    # check before upgrade
    assert stakingProxyAdmin.getImplementation() == stakingV01ImplementationBeta
    assert stakingProxyAdmin.getProxy() == stakingV01Beta

    stakingProxyAdmin.upgrade(stakingImplementation, {'from': proxyAdminOwner})

    # check after upgrade
    assert stakingProxyAdmin.getImplementation() == stakingImplementation
    assert stakingProxyAdmin.getProxy() == stakingV01Beta

    # check version after upgrade
    assert stakingV01Beta.version() == stakingImplementation.version()

    (major, minor, patch) = stakingV01Beta.versionParts()
    assert (major, minor, patch) == (1, 0, 1)

    # check version history after upgrade
    assert stakingV01Beta.versions() == 2
    assert stakingV01Beta.getVersion(0) == stakingV01ImplementationBeta.version()
    assert stakingV01Beta.getVersion(1) == stakingImplementation.version()

    info = stakingV01Beta.getVersionInfo(stakingV01Beta.getVersion(1)).dict()
    assert info['version'] == stakingImplementation.version()
    assert info['implementation'] == stakingImplementation
    assert info['activatedBy'] == proxyAdminOwner

    # test some random existing unchanged functionalities by version 02
    assert stakingV01Beta.getRegistry() == chainRegistryV01
    assert stakingV01Beta.rewardReserves() == 0

    reward_reserves = 10000 * 10 ** dip.decimals()
    dip.approve(stakingV01Beta, reward_reserves, {'from': instanceOperator})
    stakingV01Beta.refillRewardReserves(reward_reserves, {'from': instanceOperator})

    assert stakingV01Beta.rewardReserves() == reward_reserves


def test_upgraded_staking_fixture(
    instanceOperator: Account,
    stakingV01: StakingV02,
    dip: interface.IERC20Metadata,
    chainRegistryV01: ChainRegistryV01,
):
    # check version
    (major, minor, patch) = stakingV01.versionParts()
    assert (major, minor, patch) == (1, 0, 1)

    # test some random existing unchanged functionalities by version 02
    assert stakingV01.getRegistry() == chainRegistryV01
    assert stakingV01.rewardReserves() == 0

    reward_reserves = 10000 * 10 ** dip.decimals()
    dip.approve(stakingV01, reward_reserves, {'from': instanceOperator})
    stakingV01.refillRewardReserves(reward_reserves, {'from': instanceOperator})

    assert stakingV01.rewardReserves() == reward_reserves
