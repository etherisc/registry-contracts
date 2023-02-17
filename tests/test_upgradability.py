import pytest
import brownie

from brownie.network.account import Account

from brownie import (
    chain,
    OwnableProxyAdmin,
    DemoV09,
    DemoV10,
    DemoV11,
)

from scripts.util import contract_from_address

# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

def test_deploy_demo_v1(
    proxyAdminOwner: Account,
    theOutsider: Account,
    customer: Account,
    customer2: Account
):
    demoImplementationOwner = customer
    upgradableDemoOwner = customer2

    # check we have 3 different accounts
    assert upgradableDemoOwner != demoImplementationOwner
    assert upgradableDemoOwner != proxyAdminOwner
    assert demoImplementationOwner != proxyAdminOwner

    # check implementations and owner of ipml. contracts
    demoV09 = DemoV09.deploy({'from': demoImplementationOwner})
    demoV10 = DemoV10.deploy({'from': demoImplementationOwner})
    demoV11 = DemoV11.deploy({'from': demoImplementationOwner})

    assert demoV10.version() == 2 ** 32
    assert demoV11.version() == 2 ** 32 + 2 ** 16

    assert demoV10.owner() == demoImplementationOwner
    assert demoV11.owner() == demoImplementationOwner
    
    # deploy proxy and assign initial implementation and owner
    proxyAdmin = OwnableProxyAdmin.deploy(
        demoV10,
        upgradableDemoOwner,
        {'from': proxyAdminOwner})

    block_number_v10 = chain.height
    upgradableDemo = contract_from_address(
        DemoV10, 
        proxyAdmin.getProxy())

    # check that prosyAdmin and proxy are different
    assert proxyAdmin != upgradableDemo

    # check ownership of proxyAdmin and proxy contract
    assert proxyAdmin.owner() == proxyAdminOwner
    assert upgradableDemo.owner() == upgradableDemoOwner

    # check version info after deploy
    assert upgradableDemo.versions() == 1
    assert upgradableDemo.getVersion(0) == demoV10.version()

    with brownie.reverts('ERROR:VRN-010:INDEX_TOO_LARGE'):
        upgradableDemo.getVersion(1)

    info = upgradableDemo.getVersionInfo(demoV10.version()).dict()
    assert info['version'] == demoV10.version()
    assert info['versionString'] == 'v1.0.0'
    assert info['implementation'] == demoV10
    assert info['activatedBy'] == proxyAdminOwner
    assert info['activatedIn'] == block_number_v10

    # verify that upgradableDemoOwner may not upgrade to V2
    with brownie.reverts("Ownable: caller is not the owner"):
        proxyAdmin.upgrade(
            demoV11,
            {'from': upgradableDemoOwner})

    # verify that proxyAdminOwner may not upgrade to existing version
    with brownie.reverts("ERROR:PXA-011:IMPLEMENTATION_NOT_NEW"):
        proxyAdmin.upgrade(
            demoV10,
            {'from': proxyAdminOwner})

    # verify that proxyAdminOwner can upgrade to lower version number
    with brownie.reverts("ERROR:VRN-002:VERSION_NOT_INCREASING"):
        proxyAdmin.upgrade(
            demoV09,
            {'from': proxyAdminOwner})

    # verify that proxyAdminOwner can upgrade to higher version number
    proxyAdmin.upgrade(
        demoV11,
        {'from': proxyAdminOwner})    

    block_number_v11 = chain.height
    upgradableDemo = contract_from_address(
        DemoV10, 
        proxyAdmin.getProxy())

    assert block_number_v11 > block_number_v10

    # check version info after deploy
    assert upgradableDemo.versions() == 2
    assert upgradableDemo.getVersion(0) == demoV10.version()
    assert upgradableDemo.getVersion(1) == demoV11.version()

    with brownie.reverts('ERROR:VRN-010:INDEX_TOO_LARGE'):
        upgradableDemo.getVersion(2)

    info = upgradableDemo.getVersionInfo(demoV11.version()).dict()
    assert info['version'] == demoV11.version()
    assert info['versionString'] == 'v1.1.0'
    assert info['implementation'] == demoV11
    assert info['activatedBy'] == proxyAdminOwner
    assert info['activatedIn'] == block_number_v11

    assert False
