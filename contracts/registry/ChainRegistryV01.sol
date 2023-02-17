// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";

import "../shared/VersionedOwnable.sol";

type NftType is uint8;

// registers dip relevant objects for this chain
contract ChainRegistryV01 is
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

    struct RegistryInfo {
        ChainId chain;
        address registry;
    }

    struct TokenInfo {
        ChainId chain;
        address token;
    }

    event Debug1();
    event Debug2();
    event Debug3();
    event Debug4();
    event Debug5();
    event Debug6();
    event Debug7();

    mapping(uint256 tokenId => NftInfo info) private _info; // keep track of nft onchain meta data
    mapping(NftType t => bool isSupported) private _typeSupported; // which nft types are currently supported for minting
    mapping(address token => mapping(ChainId chain => bool isSupported)) private _tokenSupported; // which erc20 on which chains are currently supported for minting

    // keep track of chains
    mapping(ChainId chain => uint256 chainTokenId) private _chain;
    ChainId [] private _chainIds;

    // keep track of registries
    mapping(ChainId chain => uint256 registryTokenId) private _registry;
    mapping(uint256 registryTokenId => RegistryInfo info) private _registryInfo;
    uint256 [] private _registryTokenIds;

    ChainId private _chainId;
    uint256 private _idNext;

    // needs to be updated by all derived contracts
    Version internal _version;

    // for debugging
    uint256 [] _tokenIds;

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


    // function initialize()
    //     internal
    //     virtual 
    //     override
    //     initializer
    // {
    //     __Ownable_init();
    //     __ERC721_init(NAME, SYMBOL);
    // }


    function registerChain(ChainId chain)
        external
        onlyOwner
        returns(uint256 tokenId)
    {
        return _mintChain(owner(), chain);
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
        _chainIds.push(chain);
    }


    function registerRegistry(ChainId chain, address registry)
        external
        onlyOwner
        returns(uint256 tokenId)
    {
        _mintRegistry(owner(), chain, registry);
    }


    function _mintRegistry(address to, ChainId chain, address registry)
        internal
        returns(uint256 tokenId)
    {
        require(_chain[chain] > 0, "ERROR:ORG-020:CHAIN_NOT_SUPPORTED");
        require(_registry[chain] == 0, "ERROR:ORG-021:REGISTRY_ALREADY_REGISTERED");
        require(registry != address(0), "ERROR:ORG-022:REGISTRY_ADDRESS_ZERO");

        // mint token for the new registry
        RegistryInfo memory info = RegistryInfo(
            chain,
            registry);

        tokenId = _safeMintObject(
            to,
            chain,
            REGISTRY,
            abi.encode(info));

        // keep track of registered registries
        _registry[chain] = tokenId;
        _registryInfo[tokenId] = info;
        _registryTokenIds.push(tokenId);
    }

    // we don't need a tokens function as it would
    // return the same number as totalSupply
    // except maybe when tokens are burnt

    function getTokenId(uint256 idx) external view returns(uint256 tokenId) {
        require(idx < _tokenIds.length, "ERROR:ORG-030:INDEX_TOO_LARGE");
        return _tokenIds[idx];
    }


    function getTokenInfo(uint256 tokenId) external view returns(NftInfo memory) {
        require(_info[tokenId].id > 0, "ERROR:ORG-031:TOKEN_ID_INVALID");
        return _info[tokenId];
    }


    function getTokenMetadata(uint256 tokenId)
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
        _requireMinted(tokenId);

        NftInfo memory info = _info[tokenId];

        (
            VersionPart major,
            VersionPart minor,
            VersionPart patch
        ) = toVersionParts(info.version);

        return (
            tokenURI(tokenId),
            ownerOf(tokenId),
            toInt(info.chain),
            info.t,
            info.data,
            info.mintedIn,
            info.updatedIn,
            [major, minor, patch]
        );
    }


    function chains() external view returns(uint256 numberOfChains) {
        return _chainIds.length;
    }


    function getChainId(uint256 idx) external view returns(ChainId chain) {
        require(idx < _chainIds.length, "ERROR:ORG-040:INDEX_TOO_LARGE");
        return _chainIds[idx];
    }


    function getChainTokenId(ChainId chain) external view returns(uint256 tokenId) {
        require(_chain[chain] > 0, "ERROR:ORG-041:CHAIN_NOT_REGISTERED");
        return _chain[chain];
    }


    function registries() external view returns(uint256 numberOfRegistries) {
        return _registryTokenIds.length;
    }


    function getRegistryTokenId(uint256 idx) external view returns(uint256 tokenId) {
        require(idx < _registryTokenIds.length, "ERROR:ORG-050:INDEX_TOO_LARGE");
        return _registryTokenIds[idx];
    }


    function getRegistryForChain(ChainId chain) external view returns(uint256 tokenId) {
        require(_registry[chain] > 0, "ERROR:ORG-051:REGISTRY_NOT_REGISTERED");
        return _registry[chain];
    }


    function getRegistryInfo(uint256 tokenId) external view returns(RegistryInfo memory info) {
        require(_registryInfo[tokenId].registry != address(0), "ERROR:ORG-051:REGISTRY_NOT_REGISTERED");
        return _registryInfo[tokenId];
    }


    function tokenURI(uint256 tokenId) 
        public 
        view 
        virtual 
        override 
        returns(string memory)
    {
        _requireMinted(tokenId);
        NftInfo memory nftInfo = _info[tokenId];
        uint256 registryTokenId = _registry[nftInfo.chain];
        RegistryInfo memory registryInfo =_registryInfo[registryTokenId];

        return string(
            abi.encodePacked(
                BASE_URI, 
                toString(nftInfo.chain),
                "_erc721:",
                toString(registryInfo.registry),
                "_",
                toString(tokenId)));
    }


    function toNftType(uint256 t) public pure returns(NftType) { return NftType.wrap(uint8(t)); }

    function toString(uint256 i) public view returns(string memory) {
        return StringsUpgradeable.toString(i);
    }

    function toString(ChainId chain) public view returns(string memory) {
        return StringsUpgradeable.toString(uint24(ChainId.unwrap(chain)));
    }

    function toString(address account) public view returns(string memory) {
        return StringsUpgradeable.toHexString(account);
    }


    function _safeMintObject(
        address to,
        ChainId chain,
        NftType t,
        bytes memory data
    )
        internal 
        returns(uint256 tokenId)
    {
        require(_typeSupported[t], "OBJECT_TYPE_NOT_SUPPORTED");

        // enforce uniqe token ids over all chain id
        tokenId = _getNextTokenId();

        _tokenIds.push(tokenId);
        _safeMint(to, tokenId);

        NftInfo storage info = _info[tokenId];
        info.id = tokenId;
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
