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
    ChainRegistryV02,
    ChainNft,
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


def test_registry_facade_fixture(
    mockInstance,
    usd2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01Implementation: ChainRegistryV01,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account
):
    r = upgrade_chain_registry(chainRegistryV01, proxyAdmin, proxyAdminOwner)
    fro = {'from': registryOwner}

    mockInstance.setChainRegistry(r)
    r_facade = contract_from_address(interface.IChainRegistryFacade, r)

    r_facade.owner() == registryOwner
    r_facade.owner() == r.owner()

    nft_facade = contract_from_address(interface.IChainNftFacade, r_facade.getNft())
    assert nft_facade.name() == 'Dezentralized Insurance Protocol Registry'
    assert nft_facade.symbol() == 'DIPR'
    assert nft_facade.totalMinted() == 2 # 2 tokens: 1xchain + 1xregistry

    # check objects
    chain_id = r_facade.toChain(web3.chain_id)
    assert r_facade.objects(chain_id, r.CHAIN()) == 1
    assert r_facade.objects(chain_id, r.CHAIN()) == r.objects(chain_id, r.CHAIN())

    assert r_facade.objects(chain_id, r.REGISTRY()) == 1
    assert r_facade.objects(chain_id, r.REGISTRY()) == r.objects(chain_id, r.REGISTRY())

    assert r_facade.objects(chain_id, r.INSTANCE()) == 0
    assert r_facade.objects(chain_id, r.INSTANCE()) == r.objects(chain_id, r.INSTANCE())

    # check exists
    if web3.chain_id == 1337:
        (nft_chain_id, nft_registry_id) = (2133704, 3133704)
        assert r_facade.exists(nft_chain_id) is True
        assert r_facade.exists(nft_chain_id) == r.exists(nft_chain_id) 

        assert r_facade.exists(nft_registry_id) is True
        assert r_facade.exists(nft_registry_id) == r.exists(nft_registry_id) 

        assert r_facade.exists(nft_registry_id + 1) is False
        assert r_facade.exists(nft_registry_id + 1) == r.exists(nft_registry_id + 1)

    # check getInstanceNftId and getComponentNftId
    chain_id = r.toChain(web3.chain_id)
    instance_id = mockInstance.getInstanceId()
    riskpool_id = 7
    type_riskpool = 2 # see IInstanceServiceFacade
    state_active = 3 # see IInstanceServiceFacade

    mockInstance.setComponentInfo(riskpool_id, type_riskpool, state_active, usd2)
    r.registerToken(chain_id, usd2, 'usd2', fro)
    r.registerInstance(mockInstance.getRegistry(), 'mock instance', '', fro)
    r.registerComponent(instance_id, riskpool_id, '', fro)

    instance_nft = r.getInstanceNftId(instance_id)
    riskpool_nft = r.getComponentNftId(instance_id, riskpool_id)

    assert nft_facade.exists(instance_nft) is True
    assert nft_facade.exists(instance_nft + 1) is False
    assert nft_facade.exists(riskpool_nft) is True
    assert nft_facade.exists(riskpool_nft + 1) is False

    assert r_facade.getInstanceNftId(instance_id) == instance_nft
    assert r_facade.getComponentNftId(instance_id, riskpool_id) == riskpool_nft

    # check registerBundle and getBundleNftId
    bundle_id = 42
    bundle_state_active = 0 # enum BundleState { Active, Locked, Closed, Burned }
    bundle_funding = 1234 * 10 ** usd2.decimals()
    bundle_name = 'my bundle'
    bundle_expiry = unix_timestamp() + 14 * 24 * 3600

    mockInstance.setBundleInfo(bundle_id, riskpool_id, bundle_state_active, bundle_funding)

    # check register bundle
    r_facade.registerBundle(instance_id, riskpool_id, bundle_id, bundle_name, bundle_expiry, fro)

    bundle_nft = r.getBundleNftId(instance_id, bundle_id)
    assert nft_facade.exists(bundle_nft) is True
    assert nft_facade.exists(bundle_nft + 1) is False

    # check get bundle nft
    assert r_facade.getBundleNftId(instance_id, bundle_id) == bundle_nft

    data_before = r_facade.decodeBundleData(bundle_nft).dict()

    # check extend bundle lifetime
    lifetime_extension = 42 * 24 * 3600
    mockInstance.extendBundleLifetime(bundle_nft, lifetime_extension, {'from': proxyAdminOwner})

    data_after = r_facade.decodeBundleData(bundle_nft).dict()
    assert data_after['expiryAt']-data_before['expiryAt'] == lifetime_extension


def upgrade_chain_registry(chainRegistryV01, proxyAdmin, proxyAdminOwner):
    v2_implementation = ChainRegistryV02.deploy({'from': proxyAdminOwner})
    proxyAdmin.upgrade(v2_implementation, {'from': proxyAdminOwner})

    return contract_from_address(ChainRegistryV02, chainRegistryV01)