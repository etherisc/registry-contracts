import pytest
import brownie

from brownie.network.account import Account

from brownie import (
    history,
    interface,
    web3,
    ChainNft
)

from scripts.const import ZERO_ADDRESS


# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_nft_fixture(
    chainNftStandalone: ChainNft,
    registryOwner: Account,
    theOutsider: Account,
):
    nft = chainNftStandalone

    assert nft.name() == nft.NAME()
    assert nft.symbol() == nft.SYMBOL()
    assert nft.getRegistry() == registryOwner

    assert nft.totalSupply() == 0
    assert nft.balanceOf(theOutsider) == 0

    with brownie.reverts('ERC721: invalid token ID'):
        nft.tokenURI(1)

    with brownie.reverts('ERC721: invalid token ID'):
        nft.setURI(1, "helloworld")

    with brownie.reverts('ERC721: invalid token ID'):
        nft.burn(1)


def test_nft_mint(
    chainNftStandalone: ChainNft,
    registryOwner: Account,
    customer: Account,
    customer2: Account,
):
    nft = chainNftStandalone

    # customer attempts to mint her own token
    with brownie.reverts('ERROR:CRG-001:CALLER_NOT_REGISTRY'):
        nft.mint(customer, "helloworld", {'from': customer})

    assert nft.totalSupply() == 0
    assert nft.balanceOf(customer) == 0
    assert nft.balanceOf(customer2) == 0

    # registry mints nft on behalf of customer
    token_uri = "helloworld"
    tx = nft.mint(customer, token_uri, {'from': registryOwner})

    # check log is here
    assert 'Transfer' in tx.events

    # check minting from zero address
    evt = dict(tx.events['Transfer'])
    assert evt['from'] == ZERO_ADDRESS
    assert evt['to'] == customer

    # check token id format
    token_id = str(evt['tokenId'])

    if web3.chain_id in [1,5]:
        assert token_id[:1] == '1'
    else:
        assert token_id[:1] == '2'

    assert token_id[1:-2] == str(web3.chain_id)
    assert int(token_id[-2:]) == len(str(web3.chain_id))

    # check total and customer supply
    assert nft.totalSupply() == 1
    assert nft.balanceOf(customer) == 1
    assert nft.balanceOf(customer2) == 0

    # check customer owns newly minted token
    assert nft.tokenOfOwnerByIndex(customer, 0) == token_id
    assert nft.ownerOf(token_id) == customer

    with brownie.reverts('ERC721Enumerable: owner index out of bounds'):
        nft.tokenOfOwnerByIndex(customer, 1)

    # check token uri
    assert nft.tokenURI(token_id) == token_uri


def test_nft_set_uri(
    chainNftStandalone: ChainNft,
    registryOwner: Account,
    customer: Account,
    customer2: Account,
):
    nft = chainNftStandalone

    tx = nft.mint(customer, '', {'from': registryOwner})
    evt = dict(tx.events['Transfer'])
    token_id = str(evt['tokenId'])

    assert nft.tokenURI(token_id) == ''

    token_uri = 'ipfs://someipfcid'
    assert token_uri != ''

    # token owner attempts to set token uri
    with brownie.reverts('ERROR:CRG-001:CALLER_NOT_REGISTRY'):
        nft.setURI(token_id, token_uri, {'from': customer})

    assert nft.tokenURI(token_id) == ''

    # registry sets token uri
    nft.setURI(token_id, token_uri, {'from': registryOwner})
    assert nft.tokenURI(token_id) == token_uri

    # upate uri back to empty string
    nft.setURI(token_id, '', {'from': registryOwner})
    assert nft.tokenURI(token_id) == ''


def test_nft_burn(
    chainNftStandalone: ChainNft,
    registryOwner: Account,
    customer: Account,
    customer2: Account,
):
    nft = chainNftStandalone

    token_uri = 'ipfs://someipfcid'
    tx = nft.mint(customer, token_uri, {'from': registryOwner})
    evt = dict(tx.events['Transfer'])
    token_id = str(evt['tokenId'])

    # check total and customer supply
    assert nft.totalSupply() == 1
    assert nft.balanceOf(customer) == 1
    assert nft.balanceOf(customer2) == 0

    # check customer owns newly minted token
    assert nft.tokenOfOwnerByIndex(customer, 0) == token_id
    assert nft.ownerOf(token_id) == customer
    assert nft.tokenURI(token_id) == token_uri

    # token owner attempts to burn token
    with brownie.reverts('ERROR:CRG-001:CALLER_NOT_REGISTRY'):
        nft.burn(token_id, {'from': customer})

    assert nft.ownerOf(token_id) == customer
    assert nft.tokenURI(token_id) == token_uri

    # registry burns token of customer
    tx = nft.burn(token_id, {'from': registryOwner})

    # check burning to zero address
    evt = dict(tx.events['Transfer'])
    assert evt['from'] == customer
    assert evt['to'] == ZERO_ADDRESS
    assert evt['tokenId'] == token_id

    # check total and customer supply
    assert nft.totalSupply() == 0
    assert nft.balanceOf(customer) == 0
    assert nft.balanceOf(customer2) == 0

    # check tokenURI no longer available
    with brownie.reverts('ERC721: invalid token ID'):
        nft.tokenURI(token_id)

    # check that setting URI is disabled
    with brownie.reverts('ERC721: invalid token ID'):
        nft.setURI(token_id, token_uri, {'from': registryOwner})


def test_nft_transfer_from_simple(
    chainNftStandalone: ChainNft,
    registryOwner: Account,
    customer: Account,
    customer2: Account,
):
    nft = chainNftStandalone

    token_uri = 'ipfs://someipfcid'
    tx = nft.mint(customer, token_uri, {'from': registryOwner})
    evt = dict(tx.events['Transfer'])
    token_id = str(evt['tokenId'])

    # check total and customer supply
    assert nft.totalSupply() == 1
    assert nft.balanceOf(customer) == 1
    assert nft.balanceOf(customer2) == 0

    # attempt by customer2 to transfer nft from customer
    with brownie.reverts('ERC721: caller is not token owner or approved'):
        nft.transferFrom(customer, customer2, token_id, {'from':customer2})

    assert nft.balanceOf(customer) == 1
    assert nft.balanceOf(customer2) == 0

    # customer transfers her nft to customer2
    tx = nft.transferFrom(customer, customer2, token_id, {'from':customer})

    # check transfer log
    evt = dict(tx.events['Transfer'])
    assert evt['from'] == customer
    assert evt['to'] == customer2
    assert evt['tokenId'] == token_id

    assert nft.balanceOf(customer) == 0
    assert nft.balanceOf(customer2) == 1
    assert nft.ownerOf(token_id) == customer2


def test_nft_transfer_from_with_approval(
    chainNftStandalone: ChainNft,
    registryOwner: Account,
    customer: Account,
    customer2: Account,
):
    nft = chainNftStandalone

    token_uri = 'ipfs://someipfcid'
    tx = nft.mint(customer, token_uri, {'from': registryOwner})
    evt = dict(tx.events['Transfer'])
    token_id = str(evt['tokenId'])

    # check total and customer supply
    assert nft.totalSupply() == 1
    assert nft.balanceOf(customer) == 1
    assert nft.balanceOf(customer2) == 0

    # attempt by customer2 to transfer nft from customer
    with brownie.reverts('ERC721: caller is not token owner or approved'):
        nft.transferFrom(customer, customer2, token_id, {'from':customer2})

    assert nft.balanceOf(customer) == 1
    assert nft.balanceOf(customer2) == 0

    assert nft.getApproved(token_id) == ZERO_ADDRESS

    # approve customer2 to transfer nft from customer
    tx = nft.approve(customer2, token_id, {'from': customer})

    # check log is here
    assert 'Approval' in tx.events
    # check approval log content
    evt = dict(tx.events['Approval'])
    assert evt['owner'] == customer
    assert evt['approved'] == customer2
    assert evt['tokenId'] == token_id

    # check customer 2 is now approved to transfer nft
    assert nft.getApproved(token_id) == customer2

    # customer2 obtains nft from customer
    tx = nft.transferFrom(customer, customer2, token_id, {'from':customer2})

    # check transfer log
    evt = dict(tx.events['Transfer'])
    assert evt['from'] == customer
    assert evt['to'] == customer2
    assert evt['tokenId'] == token_id

    # check approval is reset
    assert nft.getApproved(token_id) == ZERO_ADDRESS

    # check nft balances and change of ownershiop
    assert nft.balanceOf(customer) == 0
    assert nft.balanceOf(customer2) == 1
    assert nft.ownerOf(token_id) == customer2
