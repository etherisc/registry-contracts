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
    StakingV03,
    StakingMessageHelper,
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


def test_staking_upgrade_v3(
    proxyAdminOwner: Account,
    stakingProxyAdminBase: OwnableProxyAdmin,
    stakingV01Base: StakingV01,
    stakingV01ImplementationBeta: StakingV01,
    stakingV02Implementation: StakingV02,
    stakingV03Implementation: StakingV03,
    messageHelper: StakingMessageHelper,
    stakingOwner: Account,
    dip: interface.IERC20Metadata,
    instanceOperator: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account,
):

    # check proxy admin setup
    assert stakingProxyAdminBase.getImplementation() == stakingV01ImplementationBeta
    assert stakingProxyAdminBase.getProxy() == stakingV01Base
    assert stakingProxyAdminBase.owner() == proxyAdminOwner

    # check current version
    assert stakingV01Base.version() == 1 * 2**32 + 0 * 2**16 + 0 * 2**0
    (major, minor, patch) = stakingV01Base.versionParts()
    assert (major, minor, patch) == (1, 0, 0)

    # upgrade to V02
    stakingProxyAdminBase.upgrade(stakingV02Implementation, {'from': proxyAdminOwner})

    # check V02
    assert stakingProxyAdminBase.getProxy() == stakingV01Base
    assert stakingProxyAdminBase.getImplementation() == stakingV02Implementation

    assert stakingV01Base.version() == 1 * 2**32 + 0 * 2**16 + 1 * 2**0
    (major, minor, patch) = stakingV01Base.versionParts()
    assert (major, minor, patch) == (1, 0, 1)

    # test some new functionality not available with version 02
    rate = stakingV01Base.toRate(5, -2)
    duration = stakingV01Base.YEAR_DURATION()
    stakingV03 = contract_from_address(StakingV03, stakingV01Base)

    # check that V02 reverts
    mh = StakingMessageHelper.deploy({'from': stakingOwner})
    with brownie.reverts():
        stakingV03.setMessageHelper(mh, {'from': stakingOwner})

    assert stakingV03.getMessageHelperAddress() == '0x0000000000000000000000000000000000000000'
    
    # upgrade to V03
    stakingProxyAdminBase.upgrade(stakingV03Implementation, {'from': proxyAdminOwner})

    # check new version
    assert stakingProxyAdminBase.getProxy() == stakingV01Base
    assert stakingProxyAdminBase.getImplementation() == stakingV03Implementation

    assert stakingV01Base.version() == 1 * 2**32 + 1 * 2**16 + 0 * 2**0
    (major, minor, patch) = stakingV01Base.versionParts()
    assert (major, minor, patch) == (1, 1, 0)

    # check that V03 passes
    assert stakingV03.setMessageHelper(mh, {'from': stakingOwner})
    assert stakingV03.getMessageHelperAddress() == mh


def test_upgraded_staking_fixture(
    instanceOperator: Account,
    stakingV01: StakingV03,
    stakingOwner: Account,
    dip: interface.IERC20Metadata,
    chainRegistryV01: ChainRegistryV01,
):
    # check version
    (major, minor, patch) = stakingV01.versionParts()
    assert (major, minor, patch) == (1, 1, 0)

    # test some random existing unchanged functionalities by version 02/03
    # do some stuff with reward reserves
    assert stakingV01.getRegistry() == chainRegistryV01
    assert stakingV01.rewardReserves() == 0

    reward_reserves = 10000 * 10 ** dip.decimals()
    dip.approve(stakingV01, reward_reserves, {'from': instanceOperator})
    stakingV01.refillRewardReserves(reward_reserves, {'from': instanceOperator})

    assert stakingV01.rewardReserves() == reward_reserves

    # do some stuff with reward rate
    target_id = 42
    default_rate = stakingV01.toRate(125, -3)
    stakingV01.setRewardRate(default_rate, {'from': stakingOwner})
    assert stakingV01.rewardRate() / 10**stakingV01.decimals() == 0.125
    assert stakingV01.calculateRewards(1000, stakingV01.YEAR_DURATION()) == 125
    assert stakingV01.getTargetRewardRate(target_id) == default_rate

    # test some new functionality from version 03
    # check reward rate calculation
    target_rate = stakingV01.toRate(234, -3)
    assert default_rate < target_rate

    stakingV01.setTargetRewardRate(target_id, target_rate, {'from': stakingOwner})
    assert stakingV01.getTargetRewardRate(target_id) == target_rate
