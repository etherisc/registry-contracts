// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "./IInstanceServiceFacade.sol";

interface IInstanceDataProvider {

    enum ObjectState {
        Undefined,
        Approved,
        Suspended,
        Archived
    }

    // TODO storage best practices for chainid, timestamp, ...
    struct InstanceInfo {
        bytes32 id;
        ObjectState state;
        string displayName; 
        uint256 chainId;
        address registry;
        uint256 createdAt;
        uint256 updatedAt;
    }

    struct TokenInfo {
        address token;
        uint256 chainId;
        ObjectState state;
        string symbol;
        uint8 decimals;
        uint256 createdAt;
        uint256 updatedAt;
    }

    function tokens() external view returns(uint256 numberOfTokens);
    function getTokenId(uint256 idx) external view returns(address tokenAddress, uint256 chainId);
    function getTokenInfo(address tokenAddress) external view returns(TokenInfo memory info);
    function getTokenInfo(address tokenAddress, uint256 chainId) external view returns(TokenInfo memory info);
    function isRegisteredToken(address tokenAddress) external view returns(bool isRegistered);
    function isRegisteredToken(address tokenAddress, uint256 chainId) external view returns(bool isRegistered);

    function instances() external view returns(uint256 numberOfInstances);
    function getInstanceId(uint256 idx) external view returns(bytes32 instanceId);
    function getInstanceInfo(bytes32 instanceId) external view returns(InstanceInfo memory info);
    function isRegisteredInstance(bytes32 instanceId) external view returns(bool isRegistered);

    function probeInstance(address registry)
        external 
        view 
        returns(
            bool isContract, 
            uint256 contractSize, 
            bool isValidId, 
            bytes32 istanceId, 
            IInstanceServiceFacade instanceService);
}
