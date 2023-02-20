// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;


import "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";


// needs to be in sync with definition in IInstanceService
interface IInstanceServiceFacade {

    // needs to be in sync with definition in IComponent
    enum ComponentType {
        Oracle,
        Product,
        Riskpool
    }

    // needs to be in sync with definition in IComponent
    enum ComponentState {
        Created,
        Proposed,
        Declined,
        Active,
        Paused,
        Suspended,
        Archived
    }

    function getChainId() external view returns(uint256 chainId);
    function getInstanceId() external view returns(bytes32 instanceId);
    function getInstanceOperator() external view returns(address instanceOperator);

    function getComponentType(uint256 componentId) external view returns(ComponentType componentType);
    function getComponentState(uint256 componentId) external view returns(ComponentState componentState);

    function getComponentToken(uint256 componentId) external view returns(IERC20Metadata token);

}