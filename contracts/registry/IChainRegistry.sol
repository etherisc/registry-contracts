// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "../shared/IBaseTypes.sol";

import "./IInstanceRegistryFacade.sol";
import "./IInstanceServiceFacade.sol";

type ObjectType is uint8;


interface IChainRegistry is 
    IBaseTypes 
{

    struct NftInfo {
        uint256 id;
        ChainId chain;
        ObjectType t;
        bytes data;
        Blocknumber mintedIn;
        Blocknumber updatedIn;
        Version version;
    }


    // event LogChainRegistryObjectRegistered(address token, uint256 chainId, ObjectState state, bool isNewToken);
    // event LogChainRegistryObjectStateUpdated(address token, uint256 chainId, ObjectState oldState, ObjectState newState);
    // event LogChainRegistryObjectDisplayNameUpdated(bytes32 instanceId, string oldDisplayName, string newDisplayName);

    // event LogInstanceRegistryInstanceRegistered(bytes32 instanceId, ObjectState state, bool isNewInstance);
    // event LogInstanceRegistryInstanceStateUpdated(bytes32 instanceId, ObjectState oldState, ObjectState newState);
    // event LogInstanceRegistryInstanceDisplayNameUpdated(bytes32 instanceId, string oldDisplayName, string newDisplayName);

    function registerChain(ChainId chain) external returns(uint256 nftId);
    function registerRegistry(ChainId chain, address registry) external returns(uint256 nftId);
    function registerToken(ChainId chain,address token) external returns(uint256 nftId);       


    function registerInstance(
        address instanceRegistry,
        string memory displayName
    )
        external
        returns(uint256 nftId);


    function registerComponent(
        bytes32 instanceId,
        uint256 componentId
    )
        external
        returns(uint256 nftId);


    function registerBundle(
        bytes32 instanceId,
        uint256 riskpoolId,
        uint256 bundleId,
        string memory name,
        uint256 expiryAt
    )
        external 
        returns(uint256 nftId);

    //--- view and pure functions ------------------//

    function chains() external view returns(uint256 numberOfChains);
    function getChainId(uint256 idx) external view returns(ChainId chain);
    function getNftId(ChainId chain) external view returns(uint256 nftId);

    function objects(ChainId chain, ObjectType t) external view returns(uint256 numberOfObjects);
    function getNftId(ChainId chain, ObjectType t, uint256 idx) external view returns(uint256 nftId);

    function getNftInfo(uint256 nftId) external view returns(NftInfo memory);


    function getNftMetadata(uint256 nftId)
        external 
        view 
        returns(
            string memory uri,
            address owner,
            uint256 chainId,
            ObjectType t,
            bytes memory data,
            Blocknumber mintedIn,
            Blocknumber updatedIn,
            VersionPart [3] memory v);


    function getNftId(
        ChainId chain,
        address implementation
    )
        external
        view
        returns(uint256 nftId);


    function getNftId(bytes32 instanceId)
        external
        view
        returns(uint256 nftId);


    function getComponentNftId(
        bytes32 instanceId, 
        uint256 componentId
    )
        external
        view
        returns(uint256 nftId);


    function getBundleNftId(
        bytes32 instanceId, 
        uint256 bundleId
    )
        external
        view
        returns(uint256 nftId);


    // function decodeRegistryData(uint256 nftId)

    function decodeTokenData(uint256 nftId)
        external
        view
        returns(address token);


    function decodeInstanceData(uint256 nftId)
        external
        view
        returns(
            bytes32 instanceId,
            address registry);


    function decodeComponentData(uint256 nftId)
        external
        view
        returns(
            bytes32 instanceId,
            uint256 componentId,
            address token);


    function decodeBundleData(uint256 nftId)
        external
        view
        returns(
            bytes32 instanceId,
            uint256 riskpoolId,
            uint256 bundleId,
            address token);


    function isSameType(ObjectType a, ObjectType b)
        external
        pure
        returns(bool same);


    function probeInstance(address registry)
        external 
        view 
        returns(
            bool isContract, 
            uint256 contractSize, 
            ChainId chain,
            bytes32 istanceId, 
            bool isValidId, 
            IInstanceServiceFacade instanceService);

}
