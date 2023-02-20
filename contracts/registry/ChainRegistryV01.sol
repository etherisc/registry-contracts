// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";

import "../shared/VersionedOwnable.sol";

import "./IInstanceRegistryFacade.sol";
import "./IInstanceServiceFacade.sol";

import "./IChainRegistry.sol";

// registers dip relevant objects for this chain
contract ChainRegistryV01 is
    ERC721EnumerableUpgradeable,
    VersionedOwnable,
    IChainRegistry
{
    using StringsUpgradeable for uint;
    using StringsUpgradeable for address;

    string public constant NAME = "Dezentralized Insurance Protocol Registry";
    string public constant SYMBOL = "DIPR";
    string public constant BASE_URI = "did:nft:eip155:";
    
    // responsibility of dip foundation
    ObjectType public constant UNDEFINED = ObjectType.wrap(0); // detection of uninitialized variables
    ObjectType public constant PROTOCOL = ObjectType.wrap(1); // dip ecosystem overall
    ObjectType public constant CHAIN = ObjectType.wrap(2); // dip ecosystem reach: a registry per chain
    ObjectType public constant REGISTRY = ObjectType.wrap(3); // dip ecosystem reach: a registry per chain
    ObjectType public constant TOKEN = ObjectType.wrap(4); // dip ecosystem token whitelisting (premiums, risk capital)

    // involvement of dip holders
    ObjectType public constant STAKE = ObjectType.wrap(10);

    // responsibility of instance operators
    ObjectType public constant INSTANCE = ObjectType.wrap(20);
    ObjectType public constant PRODUCT = ObjectType.wrap(21);
    ObjectType public constant ORACLE = ObjectType.wrap(22);
    ObjectType public constant RISKPOOL = ObjectType.wrap(23);

    // responsibility of product owners
    ObjectType public constant POLICY = ObjectType.wrap(30);

    // responsibility of riskpool keepers
    ObjectType public constant BUNDLE = ObjectType.wrap(40);

    mapping(uint256 nftId => NftInfo info) private _info; // keep track of nft onchain meta data
    mapping(uint256 nftId => address deployedAt) private _contract; // related contract address, if any
    mapping(ObjectType t => bool isSupported) private _typeSupported; // which nft types are currently supported for minting

    // keep track of chains
    mapping(ChainId chain => uint256 chainNftId) private _chain;
    ChainId [] private _chainIds;

    // keep track of objects per chain and type
    mapping(ChainId chain => mapping(ObjectType t => uint256 [] nftId)) private _object; // which erc20 on which chains are currently supported for minting

    // keep track of registries
    mapping(ChainId chain => uint256 registryNftId) private _registry;
    uint256 [] private _registryNftIds;

    // keep track of erc20 tokens
    mapping(ChainId chain => mapping(address token => uint256 tokenNftId)) private _token; // which erc20 on which chains are currently supported for minting
    mapping(ChainId chain => uint256 [] tokenNftIds) private _tokenNftIds;

    // keep track of instances
    mapping(bytes32 instanceId => uint256 tokenNftId) private _instance; // which erc20 on which chains are currently supported for minting
    mapping(ChainId chain => uint256 [] instanceNftIds) private _instanceNftIds;

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
        _typeSupported[INSTANCE] = true;

        // register/mint dip protocol on mainnet
        if(toInt(_chainId) == 1) {
            _registerProtocol(_chainId, newOwner);
        } else {
            _idNext++; // skip 1st id if we're not on mainnet
        }

        // register current chain and this registry
        _registerChain(_chainId, newOwner);
        _registerRegistry(_chainId, address(this), newOwner);

        transferOwnership(newOwner);
    }


    function registerChain(ChainId chain)
        external
        virtual override
        onlyOwner
        returns(uint256 nftId)
    {
        return _registerChain(chain, owner());
    }


    function registerRegistry(ChainId chain, address registry)
        external
        virtual override
        onlyOwner
        returns(uint256 nftId)
    {
        return _registerRegistry(chain, registry, owner());
    }


    function registerToken(ChainId chain, address token)
        external
        virtual override
        onlyOwner
        returns(uint256 nftId)
    {
        require(_chain[chain] > 0, "ERROR:ORG-020:CHAIN_NOT_SUPPORTED");
        require(_token[chain][token] == 0, "ERROR:ORG-020:TOKEN_ALREADY_REGISTERED");
        require(token != address(0), "ERROR:ORG-020:TOKEN_ADDRESS_ZERO");

        // mint token for the new erc20 token
        nftId = _safeMintObject(
            owner(),
            chain,
            TOKEN,
            abi.encode(token));

        // keep track of registered tokens
        _token[chain][token] = nftId;
        _tokenNftIds[chain].push(nftId);
    }


    function registerInstance(
        address instanceRegistry,
        string memory displayName
    )
        external 
        virtual override
        onlyOwner
        returns(uint256 nftId)
    {
        require(instanceRegistry != address(0), "ERROR:ORG-020:REGISTRY_ADDRESS_ZERO");

        // check instance via provided registry
        (
            bool isContract,
            , // don't care about contract size
            ChainId chain,
            bytes32 instanceId,
            bool hasValidId,
            // don't care about instanceservice
        ) = probeInstance(instanceRegistry);

        require(isContract, "ERROR:ORG-020:REGISTRY_NOT_CONTRACT");
        require(hasValidId, "ERROR:ORG-020:INSTANCE_ID_INVALID");

        // mint token for the new erc20 token
        nftId = _safeMintObject(
            owner(),
            chain,
            INSTANCE,
            abi.encode(instanceRegistry, instanceId));

        // keep track of registered instances
        _instance[instanceId] = nftId;
        _instanceNftIds[chain].push(nftId);
    }


    function probeInstance(
        address registryAddress
    )
        public
        virtual override
        view 
        returns(
            bool isContract, 
            uint256 contractSize, 
            ChainId chain,
            bytes32 instanceId,
            bool isValidId,
            IInstanceServiceFacade instanceService
        )
    {
        contractSize = _getContractSize(registryAddress);
        isContract = (contractSize > 0);

        isValidId = false;
        instanceId = bytes32(0);
        instanceService = IInstanceServiceFacade(address(0));

        if(isContract) {
            IInstanceRegistryFacade registry = IInstanceRegistryFacade(registryAddress);

            try registry.getContract("InstanceService") returns(address instanceServiceAddress) {
                instanceService = IInstanceServiceFacade(instanceServiceAddress);
                chain = toChainId(instanceService.getChainId());
                instanceId = instanceService.getInstanceId();
                isValidId = (instanceId == keccak256(abi.encodePacked(block.chainid, registry)));
            }
            catch { } // no-empty-blocks is ok here (see default return values above)
        } 
    }


    function chains() external virtual override view returns(uint256 numberOfChains) {
        return _chainIds.length;
    }

    function getChainId(uint256 idx) external virtual override view returns(ChainId chain) {
        require(idx < _chainIds.length, "ERROR:ORG-040:INDEX_TOO_LARGE");
        return _chainIds[idx];
    }

    function objects(ChainId chain, ObjectType t) external view returns(uint256 numberOfObjects) {
        return _object[chain][t].length;
    }

    function getNftId(ChainId chain, ObjectType t, uint256 idx) external view returns(uint256 nftId) {
        require(idx < _object[chain][t].length, "ERROR:ORG-040:INDEX_TOO_LARGE");
        return _object[chain][t][idx];
    }


    function getNftInfo(uint256 nftId) external virtual override view returns(NftInfo memory) {
        require(_info[nftId].id > 0, "ERROR:ORG-031:NFT_ID_INVALID");
        return _info[nftId];
    }


    function getNftMetadata(uint256 nftId)
        external
        virtual override
        view 
        returns(
            string memory uri,
            address owner,
            uint256 chainId,
            ObjectType t,
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


    function toObjectType(uint256 t) public pure returns(ObjectType) { 
        return ObjectType.wrap(uint8(t));
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


    function _registerProtocol(ChainId chain, address protocolOwner)
        internal
        virtual
        returns(uint256 nftId)
    {
        require(toInt(_chainId) == 1, "ERROR:ORG-010:NOT_MAINNET");
        require(_info[1].id == 0, "ERROR:ORG-010:PROTOCOL_ALREADY_REGISTERED");

        // mint token for the new chain
        nftId = _safeMintObject(
            protocolOwner,
            chain,
            PROTOCOL,
            "");
        
        // only one protocol in dip ecosystem
        _typeSupported[PROTOCOL] = false;
    }


    function _registerChain(ChainId chain, address chainOwner)
        internal
        virtual
        returns(uint256 nftId)
    {
        require(_chain[chain] == 0, "ERROR:ORG-010:CHAIN_ALREADY_REGISTERED");

        // mint token for the new chain
        nftId = _safeMintObject(
            chainOwner,
            chain,
            CHAIN,
            "");

        // keep track of registered chains
        _chain[chain] = nftId;
        _chainIds.push(chain);
    }


    function _registerRegistry(ChainId chain, address registry, address registryOwner)
        internal
        virtual
        returns(uint256 nftId)
    {
        require(_chain[chain] > 0, "ERROR:ORG-020:CHAIN_NOT_SUPPORTED");
        require(_registry[chain] == 0, "ERROR:ORG-021:REGISTRY_ALREADY_REGISTERED");
        require(registry != address(0), "ERROR:ORG-022:REGISTRY_ADDRESS_ZERO");

        // mint token for the new registry
        nftId = _safeMintObject(
            registryOwner,
            chain,
            REGISTRY,
            abi.encode(registry));

        // keep track of registered registries
        _registry[chain] = nftId;
        _registryNftIds.push(nftId);
    }


    function _safeMintObject(
        address to,
        ChainId chain,
        ObjectType t,
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

        // object book keeping
        _object[chain][t].push(nftId);
    }


    function _getNextTokenId() internal returns(uint256 tokenId) {
        tokenId = toInt(_chainId) * _idNext;
        _idNext++;
    }


    function _getContractSize(address contractAddress)
        internal
        view
        returns(uint256 size)
    {
        assembly {
            size := extcodesize(contractAddress)
        }
    }
}
