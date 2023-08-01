// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;


import {IChainNft, NftId, toNftId} from "../registry/IChainNft.sol";

import {IComponent} from "./IServices.sol";
import {Instance} from "./Instance.sol";

type ObjectType is uint8;

using {
    eqObjectType as ==,
    neObjectType as !=
}
    for ObjectType global;

function eqObjectType(ObjectType a, ObjectType b) pure returns(bool isSame) { return ObjectType.unwrap(a) == ObjectType.unwrap(b); }
function neObjectType(ObjectType a, ObjectType b) pure returns(bool isDifferent) { return ObjectType.unwrap(a) != ObjectType.unwrap(b); }


type ChainId is bytes5;

using {
    eqChainId as ==,
    neqChainId as !=
}
    for ChainId global;

function eqChainId(ChainId a, ChainId b) pure returns(bool isSame) { return ChainId.unwrap(a) == ChainId.unwrap(b); }
function neqChainId(ChainId a, ChainId b) pure returns(bool isDifferent) { return ChainId.unwrap(a) != ChainId.unwrap(b); }

function toChainId(uint256 chainId) pure returns(ChainId) { return ChainId.wrap(bytes5(uint40(chainId)));}
function thisChainId() view returns(ChainId) { return toChainId(block.chainid); }


contract ChainRegistry {

    enum ObjectState {
        Undefined,
        Proposed,
        Approved,
        Suspended,
        Archived,
        Burned
    }

    struct NftInfo {
        NftId id;
        ChainId chain;
        ObjectType objectType;
        ObjectState state;
        string uri;
        bytes data;
    }

    event LogDebug(uint id);

    ObjectType public constant INSTANCE = ObjectType.wrap(20);
    ObjectType public constant PRODUCT = ObjectType.wrap(21);
    ObjectType public constant ORACLE = ObjectType.wrap(22);
    ObjectType public constant RISKPOOL = ObjectType.wrap(23);


    IChainNft private _nft;

    // keep trak of nft meta data
    mapping(NftId id => NftInfo info) internal _info;

    // keep track of objects per chain and type
    mapping(ChainId chain => mapping(ObjectType t => NftId [] ids)) internal _object; // which erc20 on which chains are currently supported for minting


    function setNftContract(
        address nft,
        address newOwner
    )
        external
    {
        require(newOwner != address(0), "ERROR:CRG-040:NEW_OWNER_ZERO");

        require(address(_nft) == address(0), "ERROR:CRG-041:NFT_ALREADY_SET");
        require(nft != address(0), "ERROR:CRG-042:NFT_ADDRESS_ZERO");

        IChainNft nftContract = IChainNft(nft);
        require(nftContract.implementsIChainNft(), "ERROR:CRG-043:NFT_NOT_ICHAINNFT");

        _nft = nftContract;

        // // register/mint dip protocol on mainnet and goerli
        // if(toInt(_chainId) == 1 || toInt(_chainId) == 5) {
        //     _registerProtocol(newOwner);
        // }
        // // register current chain and this registry
        // _registerChain(_chainId, newOwner, "");
        // _registerRegistry(_chainId, address(this), newOwner, "");
    }


    function selfRegisterInstance(
        address initialOwner,
        address instanceAddress,
        string memory displayName,
        string memory uri
    )
        external 
        virtual
        returns(NftId id)
    {
        Instance instance = Instance(instanceAddress);

        bytes memory data = abi.encode(
            instanceAddress,
            instance.instanceId(),
            displayName
        );
    
        // mint token for the new erc20 token
        id = _safeMintObject(
            initialOwner,
            chainId(),
            INSTANCE,
            ObjectState.Proposed,
            uri,
            data);
    }


    function selfRegisterComponent(
        address initialOwner,
        address componentAddress,
        NftId instanceNftId
    )
        external 
        virtual
        returns(NftId id)
    {
        IComponent component = IComponent(componentAddress);
        emit LogDebug(1);

        bytes memory data = abi.encode(
            componentAddress,
            instanceNftId,
            component.name()
        );
        emit LogDebug(2);

        ObjectType obectType = PRODUCT;
        // TODO fix this
        // if(component.componentType() == IComponent.ComponentType.Oracle) {
        //     obectType = ORACLE;
        // } else if(component.componentType() == IComponent.ComponentType.Riskpool) {
        //     obectType = RISKPOOL;
        // }
        emit LogDebug(3);

        // mint token for the new erc20 token
        id = _safeMintObject(
            initialOwner,
            chainId(),
            obectType,
            ObjectState.Proposed,
            "", // uri
            data);
    }


    function chainId() public view returns(ChainId chain) {
        return toChainId(block.chainid);
    }

    function owner(NftId id) external view returns(address) {
        return _nft.ownerOf(NftId.unwrap(id));
    }


    function objects(ChainId chain, ObjectType t) public view returns(uint256 numberOfObjects) {
        return _object[chain][t].length;
    }


    function getNftInfo(NftId id) external view returns(NftInfo memory) {
        require(exists(id), "ERROR:CRG-120:NFT_ID_INVALID");
        return _info[id];
    }


    function exists(NftId id) public view returns(bool) {
        return NftId.unwrap(_info[id].id) > 0;
    }


    function _safeMintObject(
        address to,
        ChainId chain,
        ObjectType objectType,
        ObjectState state,
        string memory uri,
        bytes memory data
    )
        internal
        virtual
        returns(NftId id)
    {
        require(address(_nft) != address(0), "ERROR:CRG-350:NFT_NOT_SET");
        emit LogDebug(4);

        // mint nft
        id = toNftId(_nft.mint(to, uri));
        emit LogDebug(5);

        // store nft meta data
        NftInfo storage info = _info[id];
        info.id = id;
        info.chain = chain;
        info.objectType = objectType;
        info.state = state;
        emit LogDebug(6);

        // store data if provided        
        if(data.length > 0) {
            info.data = data;
        }
        emit LogDebug(7);

        // general object book keeping
        _object[chain][objectType].push(id);
        emit LogDebug(8);

        // object type specific book keeping
        // if(objectType == CHAIN) {
        //     _chain[chain] = id;
        //     _chainIds.push(chain);
        // } else if(objectType == REGISTRY) {
        //     _registry[chain] = id;
        // } else if(objectType == TOKEN) {
        //     (address token) = _decodeTokenData(data);
        //     _contractObject[chain][token] = id;
        // } else if(objectType == INSTANCE) {
        //     (bytes32 instanceId, address registry, ) = _decodeInstanceData(data);
        //     _contractObject[chain][registry] = id;
        //     _instance[instanceId] = id;
        // } else if(
        //     objectType == RISKPOOL
        //     || objectType == PRODUCT
        //     || objectType == ORACLE
        // ) {
        //     (bytes32 instanceId, uint256 componentId, ) = _decodeComponentData(data);
        //     _component[instanceId][componentId] = id;
        // } else if(objectType == BUNDLE) {
        //     (bytes32 instanceId, , uint256 bundleId, , , ) = _decodeBundleData(data);
        //     _bundle[instanceId][bundleId] = id;
        // }
    }


    function decodeInstanceData(NftId id)
        external
        view
        returns(
            address instanceAddress,
            bytes32 instanceId,
            string memory displayName
        )
    {
        bytes memory data = _info[id].data;

        (
            instanceAddress,
            instanceId,
            displayName
        ) = abi.decode(data, (address, bytes32, string));
    }


    function decodeComponentData(NftId id)
        external
        view
        returns(
            address componentAddress,
            NftId instanceNftId,
            string memory displayName
        )
    {
        bytes memory data = _info[id].data;

        (
            componentAddress,
            instanceNftId,
            displayName
        ) = abi.decode(data, (address, NftId, string));
    }
}