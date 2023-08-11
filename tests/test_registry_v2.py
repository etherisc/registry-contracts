import pytest
import brownie

from brownie.network.account import Account

from brownie import (
    chain,
    history,
    interface,
    web3,
    USD1,
    USD2,
    DIP,
    MockInstance,
    MockInstanceRegistry,
    OwnableProxyAdmin,
    ChainRegistryV01,
    ChainRegistryV02
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


def test_extend_bundle_lifetime(
    mockInstance: MockInstance,
    mockRegistry: MockInstanceRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account
):
    chainRegistry = upgrade_chain_registry(chainRegistryV01, proxyAdmin, proxyAdminOwner)
    mockInstance.setChainRegistry(chainRegistry)

    instance_id = mockInstance.getInstanceId()
    riskpool_id = 1

    chainRegistryV01.registerInstance(
        mockRegistry,
        'MockInstanceRegistry TEST',
        '', # uri
        {'from': registryOwner})

    # attempt direct registration of bundle
    bundle_id = 1
    bundle_name = 'my test bundle'
    bundle_expiry_at = unix_timestamp() + 14 * 24 * 3600

    # add component to dummy instance
    type_product = 1
    type_riskpool = 2

    state_created = 0
    state_active = 3
    state_paused = 4

    mockInstance.setComponentInfo(
        riskpool_id,
        type_riskpool,
        state_active,
        usd2)

    # register token
    chain_id = chainRegistryV01.toChain(mockInstance.getChainId())
    chainRegistryV01.registerToken(
            chain_id,
            usd2,
            '', # uri
            {'from': registryOwner})

    # register component
    chainRegistryV01.registerComponent(
        instance_id,
        riskpool_id,
        '', # uri
        {'from': registryOwner})

    # register bundle
    bundle_state_active = 0 # enum BundleState { Active, Locked, Closed, Burned }
    bundle_state_locked = 1
    mockInstance.setBundleInfo(
        bundle_id,
        riskpool_id,
        bundle_state_active,
        10000)

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
    assert data['displayName'] == bundle_name

    block_id = chain.height
    assert chainRegistryV01.getNftInfo(nft_id).dict()['mintedIn'] == block_id
    assert chainRegistryV01.getNftInfo(nft_id).dict()['updatedIn'] == block_id

    # verify lifetime extension via mock instance
    lifetime_extension = 42 * 24 * 3600
    tx = mockInstance.extendBundleLifetime(nft_id, lifetime_extension, {'from': proxyAdminOwner})

    assert 'LogChainRegistryObjectDataUpdated' in tx.events
    evt = tx.events['LogChainRegistryObjectDataUpdated']
    assert evt['id'] == nft_id
    assert evt['updatedBy'] == mockInstance

    block_id = chain.height
    assert chainRegistryV01.getNftInfo(nft_id).dict()['mintedIn'] == block_id - 1
    assert chainRegistryV01.getNftInfo(nft_id).dict()['updatedIn'] == block_id

    data2 = chainRegistryV01.decodeBundleData(nft_id).dict()
    assert data2['instanceId'] == data['instanceId']
    assert data2['riskpoolId'] == data['riskpoolId']
    assert data2['bundleId'] == data['bundleId']
    assert data2['token'] == data['token']
    assert data2['displayName'] == data['displayName']
    assert data2['expiryAt'] == data['expiryAt'] + lifetime_extension


def upgrade_chain_registry(chainRegistryV01, proxyAdmin, proxyAdminOwner):
    v2_implementation = ChainRegistryV02.deploy({'from': proxyAdminOwner})
    proxyAdmin.upgrade(v2_implementation, {'from': proxyAdminOwner})

    return contract_from_address(ChainRegistryV02, chainRegistryV01)