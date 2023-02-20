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
    OwnableProxyAdmin,
    ChainRegistryV01
)

from scripts.const import ZERO_ADDRESS


# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_registry_implementation(
    chainRegistryV01Implementation: ChainRegistryV01,
    theOutsider,
):
    ri = chainRegistryV01Implementation

    # check number of tokens after deploy
    assert ri.name() == ''
    assert ri.symbol() == ''
    assert ri.totalSupply() == 0

    # check current version
    assert ri.version() == 2 ** 16

    (major, minor, patch) = ri.toVersionParts(ri.version())
    assert (major, minor, patch) == (0, 1, 0)

    # check version info after deploy
    assert ri.versions() == 1
    assert ri.getVersion(0) == ri.version()

    with brownie.reverts('ERROR:VRN-010:INDEX_TOO_LARGE'):
        ri.getVersion(1)

    info = ri.getVersionInfo(ri.getVersion(0)).dict()
    assert info['version'] == ri.getVersion(0)
    assert info['versionString'] == 'v0.1.0'
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
    assert r.name() == 'Dezentralized Insurance Protocol Registry'
    assert r.symbol() == 'DIPR'

    nfts = 3 if web3.chain_id == 1 else 2
    assert r.totalSupply() == nfts
    assert r.balanceOf(ro) == nfts

    # check protocol nft (when chainid == 1)
    if web3.chain_id == 1:
        protocolTokenId = 1
        assert r.ownerOf(protocolTokenId) == ro
        assert r.getTokenId(0) == protocolTokenId

        info = r.getTokenInfo(protocolTokenId).dict()
        assert info['id'] == protocolTokenId
        assert info['t'] == r.PROTOCOL()
        assert info['chain'] == hex(web3.chain_id)
        assert info['mintedIn'] == history[-1].block_number
        assert info['updatedIn'] == history[-1].block_number
        assert info['version'] == r.version()

    # check chain nft
    chainNftId = r.getChainNftId(web3.chain_id)
    assert r.ownerOf(chainNftId) == ro
    assert r.getNftId(nfts - 2) == chainNftId

    info = r.getNftInfo(chainNftId).dict()
    assert info['id'] == chainNftId
    assert info['t'] == r.CHAIN()
    assert info['chain'] == hex(web3.chain_id)
    assert info['mintedIn'] == history[-1].block_number
    assert info['updatedIn'] == history[-1].block_number
    assert info['version'] == r.version()

    # check registry nft
    registryNftId = r.getRegistryForChain(web3.chain_id)
    assert r.ownerOf(registryNftId) == ro
    assert r.getNftId(nfts - 1) == registryNftId

    info = r.getNftInfo(registryNftId).dict()
    assert info['id'] == registryNftId
    assert info['t'] == r.REGISTRY()
    assert info['chain'] == hex(web3.chain_id)
    assert info['mintedIn'] == history[-1].block_number
    assert info['updatedIn'] == history[-1].block_number
    assert info['version'] == r.version()

    meta = r.getNftMetadata(registryNftId).dict()
    assert meta['chainId'] == web3.chain_id
    assert meta['t'] == r.REGISTRY()
    assert meta['owner'] == ro
    assert meta['mintedIn'] == info['mintedIn']
    assert meta['updatedIn'] == info['updatedIn']
    assert meta['v'] == (0, 1, 0)

    # disect uri and check its parts
    (_, _, _, uri_chain, uri_contract) = meta['uri'].split(':')
    assert uri_chain.split('_')[0] == str(web3.chain_id)
    assert uri_contract.split('_')[0] == r
    assert uri_contract.split('_')[1] == registryNftId

    # check current version
    assert r.version() == 2 ** 16

    (major, minor, patch) = ri.toVersionParts(ri.version())
    assert (major, minor, patch) == (0, 1, 0)

    # check version info after deploy
    assert r.versions() == 1
    assert r.getVersion(0) == ri.version()

    with brownie.reverts('ERROR:VRN-010:INDEX_TOO_LARGE'):
        r.getVersion(1)

    info = r.getVersionInfo(ri.getVersion(0)).dict()
    assert info['version'] == ri.getVersion(0)
    assert info['versionString'] == 'v0.1.0'
    assert info['implementation'] == chainRegistryV01Implementation
    assert info['activatedBy'] == pao


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

    with brownie.reverts('ERROR:ORG-020:CHAIN_NOT_SUPPORTED'):
        chainRegistryV01.registerToken(
            chain_id_other,
            usd1,
            {'from': registryOwner})

    with brownie.reverts('ERROR:ORG-020:TOKEN_ADDRESS_ZERO'):
        chainRegistryV01.registerToken(
            chain_id,
            ZERO_ADDRESS,
            {'from': registryOwner})

    assert chainRegistryV01.tokens(chain_id) == 0

    chainRegistryV01.registerToken(
        chain_id,
        usd1,
        {'from': registryOwner})

    assert chainRegistryV01.tokens(chain_id) == 1

    tokenNftId = chainRegistryV01.getTokenNftId(chain_id, 0)
    info = chainRegistryV01.getNftInfo(tokenNftId).dict()
    assert info['id'] == tokenNftId
    assert info['chain'] == chain_id
    assert info['t'] == chainRegistryV01.TOKEN()

    with brownie.reverts('ERROR:ORG-062:INDEX_TOO_LARGE'):
        chainRegistryV01.getTokenNftId(chain_id, 1)

    with brownie.reverts('ERROR:ORG-020:TOKEN_ALREADY_REGISTERED'):
        chainRegistryV01.registerToken(
            chain_id,
            usd1,
            {'from': registryOwner})
