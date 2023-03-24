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
from scripts.util import contract_from_address


# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_nft_facade_fixture(
    chainNftStandalone: ChainNft,
    registryOwner: Account,
    theOutsider: Account,
):
    nft = chainNftStandalone
    nft_facade = contract_from_address(interface.IChainNftFacade, nft)

    assert nft_facade.name() == nft.NAME()
    assert nft_facade.symbol() == nft.SYMBOL()
    assert nft_facade.getRegistry() == registryOwner
    assert nft_facade.totalMinted() == 0


def test_nft_facade_minting(
    chainNftStandalone: ChainNft,
    registryOwner: Account,
    customer: Account,
):
    nft = chainNftStandalone
    nft_facade = contract_from_address(interface.IChainNftFacade, nft)

    # customer attempts to mint her own token
    with brownie.reverts('ERROR:CRG-001:CALLER_NOT_REGISTRY'):
        nft_facade.mint(customer, "helloworld", {'from': customer})

    assert nft_facade.totalMinted() == 0
    assert nft_facade.totalMinted() == nft.totalMinted()

    # registry mints nft on behalf of customer
    token_uri = "helloworld"
    tx = nft_facade.mint(customer, token_uri, {'from': registryOwner})

    # get token id
    token_id = tx.return_value

    assert nft_facade.exists(token_id) is True
    assert nft_facade.exists(token_id) == nft.exists(token_id)
    assert nft_facade.exists(token_id + 1) is False

    # check token id format
    token_id = str(tx.return_value)
    if web3.chain_id in [1,5]:
        assert token_id[:1] == '1'
    else:
        assert token_id[:1] == '2'

    assert token_id[1:-2] == str(web3.chain_id)
    assert int(token_id[-2:]) == len(str(web3.chain_id))

    # check total and customer supply
    assert nft_facade.totalMinted() == 1
    assert nft_facade.totalMinted() == nft.totalMinted()

    assert nft.totalSupply() == 1
    assert nft.balanceOf(customer) == 1
