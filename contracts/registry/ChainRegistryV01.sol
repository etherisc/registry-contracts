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

    // keep trak of nft meta data
    mapping(NftId id => NftInfo info) private _info;
    mapping(ObjectType t => bool isSupported) private _typeSupported; // which nft types are currently supported for minting

    // keep track of chains
    mapping(ChainId chain => NftId id) private _chain;
    ChainId [] private _chainIds;

    // keep track of objects per chain and type
    mapping(ChainId chain => mapping(ObjectType t => NftId [] ids)) private _object; // which erc20 on which chains are currently supported for minting

    // keep track of objects with a contract address (registries, tokens, instances)
    mapping(ChainId chain => mapping(address implementation => NftId id)) private _contractObject; // which erc20 on which chains are currently supported for minting

    // keep track of instances, comonents and bundles
    mapping(bytes32 instanceId => NftId id) private _instance; // which erc20 on which chains are currently supported for minting
    mapping(bytes32 instanceId => mapping(uint256 componentId => NftId id)) private _component; // which erc20 on which chains are currently supported for minting
    mapping(bytes32 instanceId => mapping(uint256 bundleId => NftId id)) private _bundle; // which erc20 on which chains are currently supported for minting

    // registy internal data
    ChainId private _chainId;
    uint256 private _idNext;
    Version internal _version;


    modifier onlyRegisteredToken(ChainId chain, address token) {
        NftId id = _contractObject[chain][token];
        require(NftId.unwrap(id) > 0, "ERROR:CRG-001:TOKEN_NOT_REGISTERED");
        require(isSameType(_info[id].t, TOKEN), "ERROR:CRG-002:ADDRESS_NOT_TOKEN");
        _;
    }


    modifier onlyRegisteredInstance(bytes32 instanceId) {
        require(NftId.unwrap(_instance[instanceId]) > 0, "ERROR:CRG-005:INSTANCE_NOT_REGISTERED");
        _;
    }


    modifier onlyRegisteredComponent(bytes32 instanceId, uint256 componentId) {
        require(NftId.unwrap(_component[instanceId][componentId]) > 0, "ERROR:CRG-006:COMPONENT_NOT_REGISTERED");
        _;
    }


    modifier onlyActiveRiskpool(bytes32 instanceId, uint256 riskpoolId) {
        require(NftId.unwrap(_component[instanceId][riskpoolId]) > 0, "ERROR:CRG-010:RISKPOOL_NOT_REGISTERED");
        IInstanceServiceFacade instanceService = _getInstanceServiceFacade(instanceId);
        IInstanceServiceFacade.ComponentType cType = instanceService.getComponentType(riskpoolId);
        require(cType == IInstanceServiceFacade.ComponentType.Riskpool, "ERROR:CRG-011:COMPONENT_NOT_RISKPOOL");
        IInstanceServiceFacade.ComponentState state = instanceService.getComponentState(riskpoolId);
        require(state == IInstanceServiceFacade.ComponentState.Active, "ERROR:CRG-012:RISKPOOL_NOT_ACTIVE");
        _;
    }


    modifier onlySameChain(bytes32 instanceId) {
        NftId id = _instance[instanceId];
        require(NftId.unwrap(id) > 0, "ERROR:CRG-020:INSTANCE_NOT_REGISTERED");
        require(block.chainid == toInt(_info[id].chain), "ERROR:CRG-021:DIFFERENT_CHAIN_NOT_SUPPORTED");
        _;
    }

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
        _typeSupported[RISKPOOL] = true;
        _typeSupported[BUNDLE] = true;

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
        returns(NftId id)
    {
        return _registerChain(chain, owner());
    }


    function registerRegistry(ChainId chain, address registry)
        external
        virtual override
        onlyOwner
        returns(NftId id)
    {
        return _registerRegistry(chain, registry, owner());
    }


    function registerToken(ChainId chain, address token)
        external
        virtual override
        onlyOwner
        returns(NftId id)
    {
        (bytes memory data) = _getTokenData(chain, token);

        // mint token for the new erc20 token
        id = _safeMintObject(
            owner(),
            chain,
            TOKEN,
            data);
    }


    function registerInstance(
        address instanceRegistry,
        string memory displayName
    )
        external 
        virtual override
        onlyOwner
        returns(NftId id)
    {
        (
            ChainId chain,
            bytes memory data
        ) = _getInstanceData(instanceRegistry);

        // mint token for the new erc20 token
        id = _safeMintObject(
            owner(),
            chain,
            INSTANCE,
            data);
    }


    function registerComponent(
        bytes32 instanceId, 
        uint256 componentId
    )
        external 
        virtual override
        onlyRegisteredInstance(instanceId)
        onlySameChain(instanceId)
        returns(NftId id)
    {
        (
            ChainId chain,
            ObjectType t,
            bytes memory data
        ) = _getComponentData(instanceId, componentId);

        // mint token for the new erc20 token
        id = _safeMintObject(
            owner(),
            chain,
            t,
            data);
    }


    function registerBundle(
        bytes32 instanceId, 
        uint256 riskpoolId, 
        uint256 bundleId, 
        string memory name, 
        uint256 expiryAt
    )
        external
        virtual override
        onlyActiveRiskpool(instanceId, riskpoolId)
        onlySameChain(instanceId)
        returns(NftId id)
    {
        (ChainId chain, bytes memory data) = _getBundleData(instanceId, riskpoolId, bundleId);

        // mint token for the new erc20 token
        id = _safeMintObject(
            owner(),
            chain,
            BUNDLE,
            data);
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


    function exists(NftId id) public virtual override view returns(bool) {
        return NftId.unwrap(_info[id].id) > 0;
    }



    function chains() external virtual override view returns(uint256 numberOfChains) {
        return _chainIds.length;
    }

    function getChainId(uint256 idx) external virtual override view returns(ChainId chain) {
        require(idx < _chainIds.length, "ERROR:CRG-100:INDEX_TOO_LARGE");
        return _chainIds[idx];
    }


    function getNftId(ChainId chain) external view returns(NftId id) {
        return _chain[chain];
    }


    function objects(ChainId chain, ObjectType t) public view returns(uint256 numberOfObjects) {
        return _object[chain][t].length;
    }


    function getNftId(ChainId chain, ObjectType t, uint256 idx) external view returns(NftId id) {
        require(idx < _object[chain][t].length, "ERROR:CRG-110:INDEX_TOO_LARGE");
        return _object[chain][t][idx];
    }


    function getNftInfo(NftId id) external virtual override view returns(NftInfo memory) {
        require(exists(id), "ERROR:CRG-120:NFT_ID_INVALID");
        return _info[id];
    }


    function getNftMetadata(NftId id)
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
        require(exists(id), "ERROR:CRG-130:NFT_ID_INVALID");

        NftInfo memory info = _info[id];

        (
            VersionPart major,
            VersionPart minor,
            VersionPart patch
        ) = toVersionParts(info.version);

        return (
            nftURI(id),
            ownerOf(NftId.unwrap(id)),
            toInt(info.chain),
            info.t,
            info.data,
            info.mintedIn,
            info.updatedIn,
            [major, minor, patch]
        );
    }


    function getNftId(
        ChainId chain,
        address implementation
    )
        external
        virtual override
        view
        returns(NftId id)
    {
        return _contractObject[chain][implementation];
    }


    function getNftId(bytes32 instanceId)
        external
        virtual override
        view
        returns(NftId id)
    {
        return _instance[instanceId];
    }


    function getComponentNftId(bytes32 instanceId, uint256 componentId)
        external
        virtual override
        view
        returns(NftId id)
    {
        return _component[instanceId][componentId];
    }


    function getBundleNftId(bytes32 instanceId, uint256 bundleId)
        external
        virtual override
        view
        returns(NftId id)
    {
        return _bundle[instanceId][bundleId];
    }


    function decodeTokenData(NftId id)
        public
        virtual override
        view
        returns(address token)
    {
        (token) = abi.decode(_info[id].data, (address));
    }


    function decodeInstanceData(NftId id)
        public
        virtual override
        view
        returns(
            bytes32 instanceId,
            address registry
        )
    {
        (instanceId, registry) 
            = abi.decode(_info[id].data, 
                (bytes32, address));
    }


    function decodeComponentData(NftId id)
        external
        view
        returns(
            bytes32 instanceId,
            uint256 componentId,
            address token
        )
    {
        (instanceId, componentId, token) 
            = abi.decode(_info[id].data, 
                (bytes32, uint256, address));
    }


    function decodeBundleData(NftId id)
        external
        view
        returns(
            bytes32 instanceId,
            uint256 riskpoolId,
            uint256 bundleId,
            address token
        )
    {
        (instanceId, riskpoolId, bundleId, token) 
            = abi.decode(_info[id].data, 
                (bytes32, uint256, uint256, address));
    }


    function tokenURI(uint256 id) 
        public 
        view 
        override 
        returns(string memory)
    {
        return nftURI(NftId.wrap(id));
    }


    function nftURI(NftId id) 
        public 
        view 
        virtual 
        returns(string memory)
    {
        _requireMinted(NftId.unwrap(id));

        NftInfo memory info = _info[id];
        NftId registryId = _object[info.chain][REGISTRY][0];
        address registryAt = abi.decode(
            _info[registryId].data, 
            (address));

        return string(
            abi.encodePacked(
                BASE_URI, 
                toString(info.chain),
                "_erc721:",
                toString(registryAt),
                "_",
                toString(NftId.unwrap(id))));
    }


    function isSameType(ObjectType a, ObjectType b) public virtual override pure returns(bool) {
        return ObjectType.unwrap(a) == ObjectType.unwrap(b);
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
        returns(NftId id)
    {
        require(toInt(_chainId) == 1, "ERROR:CRG-200:NOT_ON_MAINNET");
        require(toInt(chain) == 1, "ERROR:CRG-201:NOT_MAINNET");
        require(objects(chain, PROTOCOL) == 0, "ERROR:CRG-202:PROTOCOL_ALREADY_REGISTERED");

        // mint token for the new chain
        id = _safeMintObject(
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
        returns(NftId id)
    {
        require(!exists(_chain[chain]), "ERROR:CRG-210:CHAIN_ALREADY_REGISTERED");

        // mint token for the new chain
        id = _safeMintObject(
            chainOwner,
            chain,
            CHAIN,
            "");
    }


    function _registerRegistry(ChainId chain, address registry, address registryOwner)
        internal
        virtual
        returns(NftId id)
    {
        require(exists(_chain[chain]), "ERROR:CRG-220:CHAIN_NOT_SUPPORTED");
        require(objects(chain, REGISTRY) == 0, "ERROR:CRG-221:REGISTRY_ALREADY_REGISTERED");
        require(registry != address(0), "ERROR:CRG-222:REGISTRY_ADDRESS_ZERO");

        // mint token for the new registry
        id = _safeMintObject(
            registryOwner,
            chain,
            REGISTRY,
            abi.encode(registry));
    }


    function _getTokenData(ChainId chain, address token)
        internal
        virtual
        view
        returns(bytes memory data)
    {
        require(exists(_chain[chain]), "ERROR:CRG-290:CHAIN_NOT_SUPPORTED");
        require(!exists(_contractObject[chain][token]), "ERROR:CRG-291:TOKEN_ALREADY_REGISTERED");
        require(token != address(0), "ERROR:CRG-292:TOKEN_ADDRESS_ZERO");

        data = _encodeTokenData(token);
    }


    function _getInstanceData(address instanceRegistry)
        internal
        virtual
        view
        returns(
            ChainId chain,
            bytes memory data
        )
    {
        require(instanceRegistry != address(0), "ERROR:CRG-300:REGISTRY_ADDRESS_ZERO");

        // check instance via provided registry
        (
            bool isContract,
            , // don't care about contract size
            ChainId chainId,
            bytes32 instanceId,
            bool hasValidId,
            // don't care about instanceservice
        ) = probeInstance(instanceRegistry);

        require(isContract, "ERROR:CRG-301:REGISTRY_NOT_CONTRACT");
        require(hasValidId, "ERROR:CRG-302:INSTANCE_ID_INVALID");
        require(exists(_chain[chainId]), "ERROR:CRG-303:CHAIN_NOT_SUPPORTED");
        require(!exists(_contractObject[chainId][instanceRegistry]), "ERROR:CRG-304:INSTANCE_ALREADY_REGISTERED");

        chain = chainId;
        data = _encodeInstanceData(instanceId, instanceRegistry);
    }


    function _getComponentData(
        bytes32 instanceId,
        uint256 componentId
    )
        internal
        virtual
        view
        returns(
            ChainId chain,
            ObjectType t,
            bytes memory data
        )
    {
        require(!exists(_component[instanceId][componentId]), "ERROR:CRG-310:COMPONENT_ALREADY_REGISTERED");

        IInstanceServiceFacade instanceService = _getInstanceServiceFacade(instanceId);
        IInstanceServiceFacade.ComponentType cType = instanceService.getComponentType(componentId);

        t = _toObjectType(cType);
        chain = toChainId(instanceService.getChainId());
        address token = address(instanceService.getComponentToken(componentId));
        require(exists(_contractObject[chain][token]), "ERROR:CRG-311:COMPONENT_TOKEN_NOT_REGISTERED");

        data = _encodeComponentData(instanceId, componentId, token);
    }


    function _getBundleData(
        bytes32 instanceId,
        uint256 riskpoolId,
        uint256 bundleId
    )
        internal
        virtual
        view
        returns(
            ChainId chain,
            bytes memory data
        )
    {
        require(!exists(_bundle[instanceId][bundleId]), "ERROR:CRG-320:BUNDLE_ALREADY_REGISTERED");

        IInstanceServiceFacade instanceService = _getInstanceServiceFacade(instanceId);
        IInstanceServiceFacade.Bundle memory bundle = instanceService.getBundle(bundleId);
        require(bundle.riskpoolId == riskpoolId, "ERROR:CRG-321:BUNDLE_RISKPOOL_MISMATCH");

        address token = address(instanceService.getComponentToken(riskpoolId));

        chain = toChainId(instanceService.getChainId());
        data = _encodeBundleData(instanceId, riskpoolId, bundleId, token);
    }


    function _encodeTokenData(address token)
        internal
        virtual
        view
        returns(bytes memory data)
    {
        return abi.encode(token);
    }


    function _encodeInstanceData(
        bytes32 instanceId,
        address registry
    )
        internal
        virtual
        view
        returns(bytes memory data)
    {
        return abi.encode(instanceId, registry);
    }


    function _encodeComponentData(
        bytes32 instanceId,
        uint256 componentId,
        address token
    )
        internal 
        virtual
        pure 
        returns(bytes memory)
    {
        return abi.encode(instanceId, componentId, token);
    }


    function _encodeBundleData(
        bytes32 instanceId,
        uint256 riskpoolId,
        uint256 bundleId,
        address token
    )
        internal 
        virtual
        pure 
        returns(bytes memory)
    {
        return abi.encode(instanceId, riskpoolId, bundleId, token);
    }


    function _getInstanceServiceFacade(bytes32 instanceId) 
        internal
        virtual
        view
        returns(IInstanceServiceFacade instanceService)
    {
        NftId id = _instance[instanceId];
        (, address registry) = decodeInstanceData(id);
        (,,,,, instanceService) = probeInstance(registry);
    }


    function _toObjectType(IInstanceServiceFacade.ComponentType cType)
        internal 
        virtual
        pure
        returns(ObjectType t)
    {
        if(cType == IInstanceServiceFacade.ComponentType.Riskpool) {
            return RISKPOOL;
        }

        if(cType == IInstanceServiceFacade.ComponentType.Product) {
            return PRODUCT;
        }

        return ORACLE;
    }


    function _safeMintObject(
        address to,
        ChainId chain,
        ObjectType t,
        bytes memory data
    )
        internal
        virtual
        returns(NftId id)
    {
        require(_typeSupported[t], "ERROR:CRG-350:OBJECT_TYPE_NOT_SUPPORTED");

        // enforce uniqe token ids over all chain id
        id = _getNextTokenId();
        _safeMint(to, NftId.unwrap(id));

        NftInfo storage info = _info[id];
        info.id = id;
        info.chain = chain;
        info.t = t;
        info.mintedIn = blockNumber();
        info.updatedIn = blockNumber();
        info.version = version();

        // store data if provided        
        if(data.length > 0) {
            info.data = data;
        }

        // general object book keeping
        _object[chain][t].push(id);

        // object type specific book keeping
        if(isSameType(t, CHAIN)) {
            _chain[chain] = id;
            _chainIds.push(chain);
        } else if(isSameType(t, TOKEN)) {
            (address token) = abi.decode(data, (address));
            _contractObject[chain][token] = id;
        } else if(isSameType(t, INSTANCE)) {
            (bytes32 instanceId, address registry) = abi.decode(data, (bytes32, address));
            _contractObject[chain][registry] = id;
            _instance[instanceId] = id;
        } else if(
            isSameType(t, RISKPOOL)
            || isSameType(t, PRODUCT)
            || isSameType(t, ORACLE)
        ) {
            (bytes32 instanceId, uint256 componentId) = abi.decode(data, (bytes32, uint256));
            _component[instanceId][componentId] = id;
        } else if(isSameType(t, BUNDLE)) {
            (bytes32 instanceId, uint256 bundleId) = abi.decode(data, (bytes32, uint256));
            _bundle[instanceId][bundleId] = id;
        }
    }


    function _getNextTokenId() internal returns(NftId id) {
        id = NftId.wrap(toInt(_chainId) * _idNext);
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
