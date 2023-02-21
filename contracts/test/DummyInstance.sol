// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "@openzeppelin/contracts/access/Ownable.sol";

import "../registry/IInstanceServiceFacade.sol";
import "./DummyRegistry.sol";

contract DummyInstance is 
    Ownable,
    IInstanceServiceFacade
{

    struct ComponentInfo {
        uint256 id;
        ComponentType t;
        ComponentState state;
        address token;
    }

    mapping(uint256 componentId => ComponentInfo info) _component;
    DummyRegistry private _registry;


    constructor() Ownable() { 
        _registry = new DummyRegistry();
        _registry.setInstanceServiceAddress(address(this));
    }


    function setComponentInfo(
        uint256 componentId,
        ComponentType t,
        ComponentState state,
        address token
    )
        external
        onlyOwner
    {
        ComponentInfo storage info = _component[componentId];
        info.id = componentId;
        info.t = t;
        info.state = state;
        info.token = token;
    }


    function getRegistry()
        external
        view
        returns(DummyRegistry registry)
    {
        return _registry;
    }


    function getChainId() external view returns(uint256 chainId) { 
        return block.chainid;
    }


    function getInstanceId() external view returns(bytes32 instanceId) {
        return keccak256(abi.encodePacked(block.chainid, _registry));
    }


    function getInstanceOperator() external view returns(address instanceOperator) {
        return owner();
    }

    function getComponentType(uint256 componentId) external view returns(ComponentType componentType) {
        require(_component[componentId].id > 0, "ERROR:DIS-010:COMPONENT_UNKNOWN");
        return _component[componentId].t;
    }

    function getComponentState(uint256 componentId) external view returns(ComponentState componentState) {
        return _component[componentId].state;
    }

    function getComponentToken(uint256 componentId) external view returns(IERC20Metadata token) {
        require(_component[componentId].token != address(0), "ERROR:DIS-020:COMPONENT_UNKNOWN");
        return IERC20Metadata(_component[componentId].token);
    }


}
