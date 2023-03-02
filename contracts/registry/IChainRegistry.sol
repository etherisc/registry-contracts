// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "../shared/IBaseTypes.sol";
import "../shared/VersionType.sol";

import "./IInstanceRegistryFacade.sol";
import "./IInstanceServiceFacade.sol";

type NftId is uint256;
type ObjectType is uint8;

using {
    eqNftId as ==,
    neNftId as !=
}
    for NftId global;

using {
    eqObjectType as ==,
    neObjectType as !=
}
    for ObjectType global;

function eqNftId(NftId a, NftId b) pure returns(bool isSame) { return NftId.unwrap(a) == NftId.unwrap(b); }
function neNftId(NftId a, NftId b) pure returns(bool isDifferent) { return NftId.unwrap(a) != NftId.unwrap(b); }
function gtz(NftId a) pure returns(bool) { return NftId.unwrap(a) > 0; }
function zeroNftId() pure returns(NftId) { return NftId.wrap(0); }

function eqObjectType(ObjectType a, ObjectType b) pure returns(bool isSame) { return ObjectType.unwrap(a) == ObjectType.unwrap(b); }
function neObjectType(ObjectType a, ObjectType b) pure returns(bool isDifferent) { return ObjectType.unwrap(a) != ObjectType.unwrap(b); }


interface IChainRegistry is 
    IBaseTypes 
{

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
        ObjectType t;
        ObjectState state;
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

    //--- state changing functions ------------------//

    function registerChain(ChainId chain) external returns(NftId id);
    function registerRegistry(ChainId chain, address registry) external returns(NftId id);
    function registerToken(ChainId chain,address token) external returns(NftId id);       


    function registerStake(
        NftId target, 
        address staker
    )
        external
        returns(NftId id);


    function registerInstance(
        address instanceRegistry,
        string memory displayName
    )
        external
        returns(NftId id);


    function registerComponent(
        bytes32 instanceId,
        uint256 componentId
    )
        external
        returns(NftId id);


    function registerBundle(
        bytes32 instanceId,
        uint256 riskpoolId,
        uint256 bundleId,
        string memory displayName,
        uint256 expiryAt
    )
        external
        returns(NftId id);


    //--- view and pure functions ------------------//

    function exists(NftId id) external view returns(bool);

    function chains() external view returns(uint256 numberOfChains);
    function getChainId(uint256 idx) external view returns(ChainId chain);
    function getNftId(ChainId chain) external view returns(NftId id);

    function objects(ChainId chain, ObjectType t) external view returns(uint256 numberOfObjects);
    function getNftId(ChainId chain, ObjectType t, uint256 idx) external view returns(NftId id);

    function getNftInfo(NftId id) external view returns(NftInfo memory);

    // get nft id for registries, tokens and instances
    function getNftId(
        ChainId chain,
        address implementation
    )
        external
        view
        returns(NftId id);

    // get nft id for a given instanceId
    function getNftId(bytes32 instanceId)
        external
        view
        returns(NftId id);

    // get nft id for specified compnent coordinates
    function getComponentNftId(
        bytes32 instanceId, 
        uint256 componentId
    )
        external
        view
        returns(NftId id);

    // get nft id for specified bundle coordinates
    function getBundleNftId(
        bytes32 instanceId, 
        uint256 bundleId
    )
        external
        view
        returns(NftId id);


    function decodeTokenData(NftId id)
        external
        view
        returns(address token);


    function decodeInstanceData(NftId id)
        external
        view
        returns(
            bytes32 instanceId,
            address registry,
            string memory displayName);


    function decodeComponentData(NftId id)
        external
        view
        returns(
            bytes32 instanceId,
            uint256 componentId,
            address token);


    function decodeBundleData(NftId id)
        external
        view
        returns(
            bytes32 instanceId,
            uint256 riskpoolId,
            uint256 bundleId,
            address token,
            string memory displayName);

    // only same chain: utility to get reference to instance service for specified instance id
    function getInstanceServiceFacade(bytes32 instanceId) 
        external
        view
        returns(IInstanceServiceFacade instanceService);

    // only same chain:  utilitiv function to probe an instance given its registry address
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
