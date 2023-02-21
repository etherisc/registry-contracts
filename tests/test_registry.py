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
    DummyInstance,
    DummyRegistry,
    OwnableProxyAdmin,
    ChainRegistryV01
)

from scripts.const import ZERO_ADDRESS
from scripts.util import unix_timestamp


# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_register_token(
    usd1: USD1,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account
):
    chain_id = chainRegistryV01.getChainId(0)

    with brownie.reverts('Ownable: caller is not the owner'):
        chainRegistryV01.registerToken(
            chain_id,
            usd1,
            {'from': theOutsider})

    chain_id_other = chainRegistryV01.toChainId(web3.chain_id + 1)

    with brownie.reverts('ERROR:CRG-290:CHAIN_NOT_SUPPORTED'):
        chainRegistryV01.registerToken(
            chain_id_other,
            usd1,
            {'from': registryOwner})

    with brownie.reverts('ERROR:CRG-292:TOKEN_ADDRESS_ZERO'):
        chainRegistryV01.registerToken(
            chain_id,
            ZERO_ADDRESS,
            {'from': registryOwner})

    tokenType = chainRegistryV01.TOKEN()
    assert chainRegistryV01.objects(chain_id, tokenType) == 0
    assert chainRegistryV01.getNftId(chain_id, usd1) == 0

    chainRegistryV01.registerToken(
        chain_id,
        usd1,
        {'from': registryOwner})

    assert chainRegistryV01.objects(chain_id, tokenType) == 1

    tokenNftId = chainRegistryV01.getNftId(chain_id, tokenType, 0)

    info = chainRegistryV01.getNftInfo(tokenNftId).dict()
    assert info['id'] == tokenNftId
    assert info['chain'] == chain_id
    assert info['t'] == chainRegistryV01.TOKEN()

    (token) = chainRegistryV01.decodeTokenData(tokenNftId)
    assert token == usd1

    with brownie.reverts('ERROR:CRG-110:INDEX_TOO_LARGE'):
        chainRegistryV01.getNftId(chain_id, tokenType, 1)

    with brownie.reverts('ERROR:CRG-291:TOKEN_ALREADY_REGISTERED'):
        chainRegistryV01.registerToken(
            chain_id,
            usd1,
            {'from': registryOwner})


def test_register_instance(
    dummyInstance: DummyInstance,
    dummyRegistry: DummyRegistry,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account
):
    with brownie.reverts('Ownable: caller is not the owner'):
        chainRegistryV01.registerInstance(
            dummyRegistry,
            "dummyRegistry TEST",
            {'from': theOutsider})

    with brownie.reverts('ERROR:CRG-300:REGISTRY_ADDRESS_ZERO'):
        chainRegistryV01.registerInstance(
            ZERO_ADDRESS,
            "dummyRegistry TEST",
            {'from': registryOwner})

    with brownie.reverts('ERROR:CRG-301:REGISTRY_NOT_CONTRACT'):
        chainRegistryV01.registerInstance(
            theOutsider,
            "dummyRegistry TEST",
            {'from': registryOwner})

    chainRegistryV01.registerInstance(
        dummyRegistry,
        "dummyRegistry TEST",
        {'from': registryOwner})

    instance_id = dummyInstance.getInstanceId()

    nft_id = chainRegistryV01.getNftId['bytes32'](instance_id)
    assert nft_id > 0

    data = chainRegistryV01.decodeInstanceData(nft_id).dict()
    assert data['instanceId'] == instance_id
    assert data['registry'] == dummyRegistry

    with brownie.reverts('ERROR:CRG-304:INSTANCE_ALREADY_REGISTERED'):
        chainRegistryV01.registerInstance(
            dummyRegistry,
            "dummyRegistry TEST",
            {'from': registryOwner})


def test_register_component(
    dummyInstance: DummyInstance,
    dummyRegistry: DummyRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account
):
    instance_id = dummyInstance.getInstanceId()
    component_id = 1

    with brownie.reverts('ERROR:CRG-005:INSTANCE_NOT_REGISTERED'):
        chainRegistryV01.registerComponent(
            instance_id,
            component_id,
            {'from': registryOwner})

    chainRegistryV01.registerInstance(
        dummyRegistry,
        "dummyRegistry TEST",
        {'from': registryOwner})

    with brownie.reverts('ERROR:DIS-010:COMPONENT_UNKNOWN'):
        chainRegistryV01.registerComponent(
            instance_id,
            component_id,
            {'from': registryOwner})

    # add component to dummy instance
    type_product = 1
    type_riskpool = 2

    state_created = 0
    state_active = 3
    state_paused = 4

    dummyInstance.setComponentInfo(
        component_id,
        type_riskpool,
        state_active,
        usd2)

    # attempt to register without registring token first
    with brownie.reverts('ERROR:CRG-311:COMPONENT_TOKEN_NOT_REGISTERED'):
        chainRegistryV01.registerComponent(
            instance_id,
            component_id,
            {'from': registryOwner})

    # register token
    chain_id = chainRegistryV01.toChainId(dummyInstance.getChainId())
    chainRegistryV01.registerToken(
            chain_id,
            usd2,
            {'from': registryOwner})

    # try again
    chainRegistryV01.registerComponent(
        instance_id,
        component_id,
        {'from': registryOwner})

    nft_id = chainRegistryV01.getComponentNftId(instance_id, component_id)
    assert nft_id > 0

    data = chainRegistryV01.decodeComponentData(nft_id).dict()
    assert data['instanceId'] == instance_id
    assert data['componentId'] == component_id
    assert data['token'] == usd2

    with brownie.reverts('ERROR:CRG-310:COMPONENT_ALREADY_REGISTERED'):
        chainRegistryV01.registerComponent(
            instance_id,
            component_id,
            {'from': registryOwner})


def test_register_bundle(
    dummyInstance: DummyInstance,
    dummyRegistry: DummyRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account
):
    instance_id = dummyInstance.getInstanceId()
    riskpool_id = 1
    riskpool_id2 = 2

    chainRegistryV01.registerInstance(
        dummyRegistry,
        "dummyRegistry TEST",
        {'from': registryOwner})

    # attempt direct registration of bundle
    bundle_id = 1
    bundle_id2 = 2
    bundle_name = 'my test bundle'
    bundle_expiry_at = unix_timestamp() + 14 * 24 * 3600

    with brownie.reverts('ERROR:CRG-010:RISKPOOL_NOT_REGISTERED'):
        chainRegistryV01.registerBundle(
            instance_id,
            riskpool_id,
            bundle_id,
            bundle_name,
            bundle_expiry_at,
            {'from': theOutsider})

    # add component to dummy instance
    type_product = 1
    type_riskpool = 2

    state_created = 0
    state_active = 3
    state_paused = 4

    dummyInstance.setComponentInfo(
        riskpool_id,
        type_riskpool,
        state_paused,
        usd2)

    # register token
    chain_id = chainRegistryV01.toChainId(dummyInstance.getChainId())
    chainRegistryV01.registerToken(
            chain_id,
            usd2,
            {'from': registryOwner})

    # register component
    chainRegistryV01.registerComponent(
        instance_id,
        riskpool_id,
        {'from': registryOwner})

    # attempt to register bundle for paused riskpool
    with brownie.reverts('ERROR:CRG-012:RISKPOOL_NOT_ACTIVE'):
        chainRegistryV01.registerBundle(
            instance_id,
            riskpool_id,
            bundle_id,
            bundle_name,
            bundle_expiry_at,
            {'from': theOutsider})

    # activate riskpool
    dummyInstance.setComponentInfo(
        riskpool_id,
        type_riskpool,
        state_active,
        usd2)

    dummyInstance.setComponentInfo(
        riskpool_id2,
        type_riskpool,
        state_active,
        usd2)

    # try before bundle is "created"
    with brownie.reverts('ERROR:DIS-030:BUNDLE_DOES_NOT_EXIST'):
        chainRegistryV01.registerBundle(
            instance_id,
            riskpool_id,
            bundle_id,
            bundle_name,
            bundle_expiry_at,
            {'from': theOutsider})

    # register bundle
    dummyInstance.setBundleInfo(
        bundle_id,
        riskpool_id,
        10000)

    dummyInstance.setBundleInfo(
        bundle_id2,
        riskpool_id2,
        20000)

    # try to register bundle with wrong riskpool
    with brownie.reverts('ERROR:CRG-321:BUNDLE_RISKPOOL_MISMATCH'):
        chainRegistryV01.registerBundle(
            instance_id,
            riskpool_id,
            bundle_id2,
            bundle_name,
            bundle_expiry_at,
            {'from': theOutsider})

    # try again
    chainRegistryV01.registerBundle(
        instance_id,
        riskpool_id,
        bundle_id,
        bundle_name,
        bundle_expiry_at,
        {'from': theOutsider})

    nft_id = chainRegistryV01.getBundleNftId(instance_id, bundle_id)
    assert nft_id > 0

    data = chainRegistryV01.decodeBundleData(nft_id).dict()
    assert data['instanceId'] == instance_id
    assert data['riskpoolId'] == riskpool_id
    assert data['bundleId'] == bundle_id
    assert data['token'] == usd2

    with brownie.reverts('ERROR:CRG-320:BUNDLE_ALREADY_REGISTERED'):
        chainRegistryV01.registerBundle(
            instance_id,
            riskpool_id,
            bundle_id,
            bundle_name,
            bundle_expiry_at,
            {'from': theOutsider})
