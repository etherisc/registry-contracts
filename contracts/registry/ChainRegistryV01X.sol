// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";

import "../shared/VersionedOwnable.sol";

type NftType is uint8;

// registers dip relevant objects for this chain
contract ChainRegistryV01X is
    ERC721EnumerableUpgradeable,
    VersionedOwnable
{
    using StringsUpgradeable for uint;
    using StringsUpgradeable for address;

    string public constant NAME = "Dezentralized Insurance Protocol Registry";
    string public constant SYMBOL = "DIPR";
    string public constant BASE_URI = "did:nft:eip155:";
    
    // responsibility of dip foundation
    NftType public constant UNDEFINED = NftType.wrap(0); // detection of uninitialized variables
    NftType public constant PROTOCOL = NftType.wrap(1); // dip ecosystem overall
    NftType public constant CHAIN = NftType.wrap(2); // dip ecosystem reach: a registry per chain
    NftType public constant REGISTRY = NftType.wrap(3); // dip ecosystem reach: a registry per chain
    NftType public constant TOKEN = NftType.wrap(4); // dip ecosystem token whitelisting (premiums, risk capital)

    // involvement of dip holders
    NftType public constant STAKE = NftType.wrap(10);

    // responsibility of instance operators
    NftType public constant INSTANCE = NftType.wrap(20);
    NftType public constant PRODUCT = NftType.wrap(21);
    NftType public constant ORACLE = NftType.wrap(22);
    NftType public constant RISKPOOL = NftType.wrap(23);

    // responsibility of product owners
    NftType public constant POLICY = NftType.wrap(30);

    // responsibility of riskpool keepers
    NftType public constant BUNDLE = NftType.wrap(40);

    struct NftInfo {
        uint256 id;
        ChainId chain;
        NftType t;
        bytes data;
        Blocknumber mintedIn;
        Blocknumber updatedIn;
        Version version;
    }

    mapping(uint256 nftId => NftInfo info) private _info; // keep track of nft onchain meta data
    mapping(uint256 nftId => address deployedAt) private _contract; // related contract address, if any
    mapping(NftType t => bool isSupported) private _typeSupported; // which nft types are currently supported for minting

    // keep track of chains
    mapping(ChainId chain => uint256 chainNftId) private _chain;
    ChainId [] private _chainNftIds;

    // keep track of registries
    mapping(ChainId chain => uint256 registryNftId) private _registry;
    uint256 [] private _registryNftIds;

    // keep track of erc20 tokens
    mapping(ChainId chain => mapping(address token => uint256 tokenNftId)) private _token; // which erc20 on which chains are currently supported for minting
    mapping(ChainId chain => uint256 [] tokenNftIds) private _tokenNftIds;

    // registy data
    ChainId private _chainId;
    uint256 private _idNext;

    // needs to be updated by all derived contracts
    Version internal _version;

    // for debugging
    uint256 [] _nftIds;

    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toPart(0), toPart(1), toPart(0));
    }

    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activateAndSetOwner(address implementation, address newOwner)
        external
        virtual override
        initializer
    {
        // ensure proper version history
        _activate(implementation);

        // initialize open zeppelin contracts
        __Ownable_init();
        __ERC721_init(NAME, SYMBOL);

        // set main internal variables
        _version = version();
        _chainId = toChainId(block.chainid);
        _idNext = 1;

        // set types supported by this version
        _typeSupported[PROTOCOL] = true;
        _typeSupported[CHAIN] = true;
        _typeSupported[REGISTRY] = true;
        _typeSupported[TOKEN] = true;

        // register/mint dip protocol on mainnet
        if(toInt(_chainId) == 1) {
            _mintProtocol(newOwner, _chainId);
        } else {
            _idNext++; // skip 1st id if we're not on mainnet
        }

        // register current chain and this registry
        _mintChain(newOwner, _chainId);
        _mintRegistry(newOwner, _chainId, address(this));

        transferOwnership(newOwner);
    }


    function registerChain(ChainId chain)
        external
        onlyOwner
        returns(uint256 nftId)
    {
        return _mintChain(owner(), chain);
    }


    function registerRegistry(ChainId chain, address registry)
        external
        onlyOwner
        returns(uint256 nftId)
    {
        _mintRegistry(owner(), chain, registry);
    }


    function registerToken(ChainId chain, address token)
        external
        onlyOwner
        returns(uint256 nftId)
    {
        _mintToken(owner(), chain, token);
    }


    function chains() external view returns(uint256 numberOfChains) {
        return _chainNftIds.length;
    }


    function getChainId(uint256 idx) external view returns(ChainId chain) {
        require(idx < _chainNftIds.length, "ERROR:ORG-040:INDEX_TOO_LARGE");
        return _chainNftIds[idx];
    }


    function getChainNftId(ChainId chain) external view returns(uint256 tokenId) {
        require(_chain[chain] > 0, "ERROR:ORG-041:CHAIN_NOT_REGISTERED");
        return _chain[chain];
    }


    function registries() external view returns(uint256 numberOfRegistries) {
        return _registryNftIds.length;
    }


    function getRegistryNftId(uint256 idx) external view returns(uint256 nftId) {
        require(idx < _registryNftIds.length, "ERROR:ORG-050:INDEX_TOO_LARGE");
        return _registryNftIds[idx];
    }


    function getRegistryForChain(ChainId chain) external view returns(uint256 nftId) {
        require(_registry[chain] > 0, "ERROR:ORG-051:REGISTRY_NOT_REGISTERED");
        return _registry[chain];
    }


    function tokens(ChainId chain) external view returns(uint numberOfTokens) {
        require(_chain[chain] > 0, "ERROR:ORG-060:CHAIN_NOT_REGISTERED");
        return _tokenNftIds[chain].length;
    }


    function getTokenNftId(ChainId chain, uint256 idx) external view returns(uint256 nftId) {
        require(_chain[chain] > 0, "ERROR:ORG-061:CHAIN_NOT_REGISTERED");
        require(idx < _tokenNftIds[chain].length, "ERROR:ORG-062:INDEX_TOO_LARGE");
        return _tokenNftIds[chain][idx];
    }


    function nfts() external view returns(uint256 numberOfNfts) {
        return totalSupply();
    }

    function getNftId(uint256 idx) external view returns(uint256 nftId) {
        require(idx < _nftIds.length, "ERROR:ORG-030:INDEX_TOO_LARGE");
        return _nftIds[idx];
    }


    function getNftInfo(uint256 nftId) external view returns(NftInfo memory) {
        require(_info[nftId].id > 0, "ERROR:ORG-031:NFT_ID_INVALID");
        return _info[nftId];
    }


    function getNftMetadata(uint256 nftId)
        external 
        view 
        returns(
            string memory uri,
            address owner,
            uint256 chainId,
            NftType t,
            bytes memory data,
            Blocknumber mintedIn,
            Blocknumber updatedIn,
            VersionPart [3] memory v
        )
    {
        _requireMinted(nftId);

        NftInfo memory info = _info[nftId];

        (
            VersionPart major,
            VersionPart minor,
            VersionPart patch
        ) = toVersionParts(info.version);

        return (
            nftURI(nftId),
            ownerOf(nftId),
            toInt(info.chain),
            info.t,
            info.data,
            info.mintedIn,
            info.updatedIn,
            [major, minor, patch]
        );
    }


    function tokenURI(uint256 nftId) 
        public 
        view 
        override 
        returns(string memory)
    {
        return nftURI(nftId);
    }


    function nftURI(uint256 nftId) 
        public 
        view 
        virtual 
        returns(string memory)
    {
        _requireMinted(nftId);

        NftInfo memory info = _info[nftId];
        uint256 registryNftId = _registry[info.chain];
        address registryAt = abi.decode(
            _info[registryNftId].data, 
            (address));

        return string(
            abi.encodePacked(
                BASE_URI, 
                toString(info.chain),
                "_erc721:",
                toString(registryAt),
                "_",
                toString(nftId)));
    }


    function toNftType(uint256 t) public pure returns(NftType) { 
        return NftType.wrap(uint8(t));
    }

    function toString(uint256 i) public view returns(string memory) {
        return StringsUpgradeable.toString(i);
    }

    function toString(ChainId chain) public view returns(string memory) {
        return StringsUpgradeable.toString(uint24(ChainId.unwrap(chain)));
    }

    function toString(address account) public view returns(string memory) {
        return StringsUpgradeable.toHexString(account);
    }


    function _mintProtocol(address to, ChainId chain)
        internal
        returns(uint256 tokenId)
    {
        require(toInt(_chainId) == 1, "ERROR:ORG-010:NOT_MAINNET");
        require(_info[1].id == 0, "ERROR:ORG-010:PROTOCOL_ALREADY_REGISTERED");

        // mint token for the new chain
        tokenId = _safeMintObject(
            to,
            chain,
            PROTOCOL,
            "");
        
        // only one protocol in dip ecosystem
        _typeSupported[PROTOCOL] = false;
    }


    function _mintChain(address to, ChainId chain)
        internal
        returns(uint256 tokenId)
    {
        require(_chain[chain] == 0, "ERROR:ORG-010:CHAIN_ALREADY_REGISTERED");

        // mint token for the new chain
        tokenId = _safeMintObject(
            to,
            chain,
            CHAIN,
            "");

        // keep track of registered chains
        _chain[chain] = tokenId;
        _chainNftIds.push(chain);
    }


    function _mintRegistry(address to, ChainId chain, address registry)
        internal
        returns(uint256 nftId)
    {
        require(_chain[chain] > 0, "ERROR:ORG-020:CHAIN_NOT_SUPPORTED");
        require(_registry[chain] == 0, "ERROR:ORG-021:REGISTRY_ALREADY_REGISTERED");
        require(registry != address(0), "ERROR:ORG-022:REGISTRY_ADDRESS_ZERO");

        // mint token for the new registry
        nftId = _safeMintObject(
            to,
            chain,
            REGISTRY,
            abi.encode(registry));

        // keep track of registered registries
        _registry[chain] = nftId;
        _registryNftIds.push(nftId);
    }


    function _mintToken(address to, ChainId chain, address token)
        internal
        returns(uint256 nftId)
    {
        require(_chain[chain] > 0, "ERROR:ORG-020:CHAIN_NOT_SUPPORTED");
        require(_token[chain][token] == 0, "ERROR:ORG-020:TOKEN_ALREADY_REGISTERED");
        require(token != address(0), "ERROR:ORG-020:TOKEN_ADDRESS_ZERO");

        // mint token for the new erc20 token
        nftId = _safeMintObject(
            to,
            chain,
            TOKEN,
            abi.encode(token));

        // keep track of registered tokens
        _token[chain][token] = nftId;
        _tokenNftIds[chain].push(nftId);
    }


    function _safeMintObject(
        address to,
        ChainId chain,
        NftType t,
        bytes memory data
    )
        internal 
        returns(uint256 nftId)
    {
        require(_typeSupported[t], "OBJECT_TYPE_NOT_SUPPORTED");

        // enforce uniqe token ids over all chain id
        nftId = _getNextTokenId();

        _nftIds.push(nftId);
        _safeMint(to, nftId);

        NftInfo storage info = _info[nftId];
        info.id = nftId;
        info.chain = chain;
        info.t = t;
        info.mintedIn = blockNumber();
        info.updatedIn = blockNumber();
        info.version = version();

        // store data if provided        
        if(data.length > 0) {
            info.data = data;
        }
    }


    function _getNextTokenId() internal returns(uint256 tokenId) {
        tokenId = toInt(_chainId) * _idNext;
        _idNext++;
    }
}
