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
)

from scripts.const import ZERO_ADDRESS
from scripts.util import contract_from_address

# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_registry_implementation(
    chainRegistryV01Implementation: ChainRegistryV01,
    theOutsider,
):
    ri = chainRegistryV01Implementation

    # check current version
    assert ri.version() == 1 * 2**32 + 0 * 2**16 + 0 * 2**0

    (major, minor, patch) = ri.versionParts()
    assert (major, minor, patch) == (1, 0, 0)

    # check version info after deploy
    assert ri.versions() == 1
    assert ri.getVersion(0) == ri.version()

    with brownie.reverts('ERROR:VRN-010:INDEX_TOO_LARGE'):
        ri.getVersion(1)

    info = ri.getVersionInfo(ri.getVersion(0)).dict()
    assert info['version'] == ri.getVersion(0)
    assert info['implementation'] == chainRegistryV01Implementation
    assert info['activatedBy'] == theOutsider


def test_registry_basics(
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01Implementation: ChainRegistryV01,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account
):
    pa = proxyAdmin
    pao = proxyAdminOwner
    ri = chainRegistryV01Implementation
    r = chainRegistryV01
    ro = registryOwner
    o = theOutsider

    # check accounts
    assert pa != ri
    assert pa != ro
    assert pao != ro
    assert ro != o

    # check ownerships
    assert pao == pa.owner()
    assert pao != ri.owner()
    assert pao != r.owner()
    assert ri.owner() == o
    assert ri.owner() != r.owner()
    assert r.owner() == ro

    # check proxy admin
    assert pa.getImplementation() == ri

    # check number of tokens after deploy
    nft = contract_from_address(ChainNft, r.getNft())

    assert nft.name() == 'Dezentralized Insurance Protocol Registry'
    assert nft.symbol() == 'DIPR'

    nfts = 3 if web3.chain_id in [1, 1337] else 2
    assert nft.totalSupply() == nfts
    assert nft.balanceOf(ro) == nfts

    protocolTokenId = 1101

    # check protocol nft (when chainid == 1)
    if web3.chain_id == 1:
        assert r.exists(protocolTokenId)
        assert r.objects(1, r.PROTOCOL()) == 1
        assert r.getNftId(1, r.PROTOCOL(), 0) == protocolTokenId
        assert r.ownerOf(protocolTokenId) == ro

        info = r.getNftInfo(protocolTokenId).dict()
        assert info['id'] == protocolTokenId
        assert info['objectType'] == r.PROTOCOL()
        assert info['chain'] == hex(web3.chain_id)
        assert info['mintedIn'] == history[-1].block_number
        assert info['updatedIn'] == history[-1].block_number
        assert info['version'] == r.version()
    else:
        assert r.exists(protocolTokenId) is False
        assert r.objects(1, r.PROTOCOL()) == 0


    # check chain nft
    chainId = r.toChain(web3.chain_id)
    chainNftId = r.getChainNftId(chainId)
    assert r.ownerOf(chainNftId) == ro

    expected_block_number = history[-1].block_number
    info = r.getNftInfo(chainNftId).dict()
    assert info['id'] == chainNftId
    assert info['objectType'] == r.CHAIN()
    assert info['chain'] == hex(web3.chain_id)
    assert info['mintedIn'] == expected_block_number
    assert info['updatedIn'] == expected_block_number
    assert info['version'] == r.version()

    # check registry nft
    registryNftId = r.getNftId(chainId, r.REGISTRY(), 0)
    assert r.ownerOf(registryNftId) == ro

    info = r.getNftInfo(registryNftId).dict()
    assert info['id'] == registryNftId
    assert info['objectType'] == r.REGISTRY()
    assert info['chain'] == hex(web3.chain_id)
    assert info['mintedIn'] == expected_block_number
    assert info['updatedIn'] == expected_block_number
    assert info['version'] == r.version()

    # disect uri and check its parts
    nft_uri = r.tokenDID(registryNftId)
    (_, _, _, uri_chain, uri_contract) = nft_uri.split(':')
    assert uri_chain.split('_')[0] == str(web3.chain_id)
    assert uri_contract.split('_')[0] == r
    assert uri_contract.split('_')[1] == registryNftId

    # check nft id composition
    chain_digits = len(str(web3.chain_id))
    digits_part = str(registryNftId)[-2:]
    chain_part = str(registryNftId)[-(chain_digits + 2):-2]
    index_part = str(registryNftId)[:-(chain_digits + 2)]

    assert int(index_part + chain_part + digits_part) == registryNftId
    assert int(index_part) > 1
    assert int(chain_part) == web3.chain_id
    assert int(digits_part) == chain_digits

    # check current version
    assert r.version() == 1 * 2**32 + 0 * 2**16 + 0 * 2**0

    (major, minor, patch) = ri.versionParts()
    assert (major, minor, patch) == (1, 0, 0)

    # check version info after deploy
    assert r.versions() == 1
    assert r.getVersion(0) == ri.version()

    with brownie.reverts('ERROR:VRN-010:INDEX_TOO_LARGE'):
        r.getVersion(1)

    info = r.getVersionInfo(ri.getVersion(0)).dict()
    assert info['version'] == ri.getVersion(0)
    assert info['implementation'] == chainRegistryV01Implementation
    assert info['activatedBy'] == pao
