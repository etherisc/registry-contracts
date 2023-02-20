// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "../shared/IBaseTypes.sol";


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
    // 
    // event LogChainRegistryObjectRegistered(address token, uint256 chainId, ObjectState state, bool isNewToken);
    // event LogChainRegistryObjectStateUpdated(address token, uint256 chainId, ObjectState oldState, ObjectState newState);
    // event LogChainRegistryObjectDisplayNameUpdated(bytes32 instanceId, string oldDisplayName, string newDisplayName);

    // event LogInstanceRegistryInstanceRegistered(bytes32 instanceId, ObjectState state, bool isNewInstance);
    // event LogInstanceRegistryInstanceStateUpdated(bytes32 instanceId, ObjectState oldState, ObjectState newState);
    // event LogInstanceRegistryInstanceDisplayNameUpdated(bytes32 instanceId, string oldDisplayName, string newDisplayName);

    function register(ChainId chain, address implementation) external returns(uint256 nftId);
}
