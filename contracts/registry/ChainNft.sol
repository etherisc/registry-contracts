// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";

contract ChainNft is
    ERC721Enumerable
{
    string public constant NAME = "Dezentralized Insurance Protocol Registry";
    string public constant SYMBOL = "DIPR";

    // remember registry
    address private _registry;

    // remember token uri
    mapping(uint256 tokenId => string uri) private _uri;

    // only used for _getNextTokenId
    uint256 internal _chainIdInt; 
    uint256 internal _chainIdDigits;
    uint256 internal _chainIdMultiplier;
    uint256 internal _idNext;


    modifier onlyRegistry() {
        require(msg.sender == _registry, "ERROR:CRG-001:CALLER_NOT_REGISTRY");
        _;
    }


    constructor(address registry)
        ERC721(NAME, SYMBOL)
    {
        require(registry != address(0), "ERROR:CRG-010:REGISTRY_ZERO");

        _registry = registry;

        _chainIdInt = block.chainid;
        _chainIdDigits = _countDigits(_chainIdInt);
        _chainIdMultiplier = 10 ** _chainIdDigits;
        _idNext = 1;
    }


    function mint(
        address to,
        string memory uri
    )
        external
        onlyRegistry
        returns(uint256 tokenId)
    {
        tokenId = _getNextTokenId();
        _safeMint(to, tokenId);

        if(bytes(uri).length > 0) {
            _uri[tokenId] = uri;
        }
    }


    function burn(uint256 tokenId)
        external
        onlyRegistry
    {
        _requireMinted(tokenId);
        _burn(tokenId);
        delete _uri[tokenId];
    }


    function setURI(uint256 tokenId, string memory uri)
        external
        onlyRegistry
    {
        _requireMinted(tokenId);
        _uri[tokenId] = uri;
    }


    function tokenURI(uint256 tokenId)
        public
        view
        override 
        returns(string memory)
    {
        _requireMinted(tokenId);
        return _uri[tokenId];
    }


    function getRegistry()
        external
        view
        returns(address registry)
    {
        return _registry;
    }


    // requirement: each chain registry produces token ids that
    // are guaranteed to not collide with any token id genereated
    // on a different chain
    //
    // format concat(counter,chainid,2 digits for len-of-chain-id)
    // restriction chainid up to 99 digits
    // decode: from right to left:
    // - 2 right most digits encode length of chainid
    // - move number of digits to left as determined above (-> chainid)
    // - the reminder to the left is the counter
    // examples
    // 1101
    // ^^ ^
    // || +- 1-digit chain id
    // |+-- chain id = 1 (mainnet)
    // +-- 1st token id on mainnet
    // (1 * 10 ** 1 + 1) * 100 + 1
    // 42987654321010
    // ^ ^          ^
    // | |          +- 10-digit chain id
    // | +-- chain id = 9876543210 (hypothetical chainid)
    // +-- 42nd token id on this chain
    // (42 * 10 ** 10 + 9876543210) * 100 + 10
    // (index * 10 ** digits + chainid) * 100 + digits (1 < digits < 100)

    function _getNextTokenId() internal returns(uint256 id) {
        id = (_idNext * _chainIdMultiplier + _chainIdInt) * 100 + _chainIdDigits;
        _idNext++;
    }


    function _countDigits(uint256 num)
        internal 
        pure 
        returns (uint256 count)
    {
        count = 0;
        while (num != 0) {
            count++;
            num /= 10;
        }
    }
}