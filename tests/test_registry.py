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

    with brownie.reverts('ERROR:CRG-040:CHAIN_NOT_SUPPORTED'):
        chainRegistryV01.registerToken(
            chain_id_other,
            usd1,
            {'from': registryOwner})

    with brownie.reverts('ERROR:CRG-042:TOKEN_ADDRESS_ZERO'):
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
    assert chainRegistryV01.getNftId(chain_id, usd1) == tokenNftId

    info = chainRegistryV01.getNftInfo(tokenNftId).dict()
    assert info['id'] == tokenNftId
    assert info['chain'] == chain_id
    assert info['t'] == chainRegistryV01.TOKEN()

    obj = chainRegistryV01.getContractObject(tokenNftId).dict()
    assert obj['id'] == info['id']
    assert obj['chain'] == info['chain']
    assert obj['t'] == info['t']
    assert obj['implementation'] == usd1

    with brownie.reverts('ERROR:CRG-110:INDEX_TOO_LARGE'):
        chainRegistryV01.getNftId(chain_id, tokenType, 1)

    with brownie.reverts('ERROR:CRG-041:TOKEN_ALREADY_REGISTERED'):
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

    with brownie.reverts('ERROR:CRG-050:REGISTRY_ADDRESS_ZERO'):
        chainRegistryV01.registerInstance(
            ZERO_ADDRESS,
            "dummyRegistry TEST",
            {'from': registryOwner})

    with brownie.reverts('ERROR:CRG-051:REGISTRY_NOT_CONTRACT'):
        chainRegistryV01.registerInstance(
            theOutsider,
            "dummyRegistry TEST",
            {'from': registryOwner})

    chainRegistryV01.registerInstance(
        dummyRegistry,
        "dummyRegistry TEST",
        {'from': registryOwner})

    instance_id = dummyInstance.getInstanceId()

    nft_id = chainRegistryV01.getNftId(instance_id)
    assert nft_id > 0

    obj = chainRegistryV01.getContractObject(nft_id).dict()
    assert obj['id'] == nft_id
    assert obj['chain'] == chainRegistryV01.toChainId(web3.chain_id)
    assert obj['t'] == chainRegistryV01.INSTANCE()
    assert obj['implementation'] == dummyRegistry


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
    with brownie.reverts('ERROR:CRG-060:COMPONENT_TOKEN_NOT_REGISTERED'):
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

    obj = chainRegistryV01.getInstanceObject(nft_id).dict()
    assert obj['id'] == nft_id
    assert obj['chain'] == chainRegistryV01.toChainId(web3.chain_id)
    assert obj['t'] == chainRegistryV01.RISKPOOL()
    assert obj['instanceId'] == instance_id
    assert obj['objectId'] == component_id
    assert obj['token'] == usd2

