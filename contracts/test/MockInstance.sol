// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";

import "../registry/IInstanceServiceFacade.sol";
import "./MockRegistry.sol";

contract MockInstance is 
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
    mapping(uint256 bundleId => Bundle bundle) _bundle;
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


    function setBundleInfo(
        uint256 bundleId,
        uint256 riskpoolId,
        uint256 capital
    )
        external
        onlyOwner
    {
        Bundle storage bundle = _bundle[bundleId];
        bundle.id = bundleId;
        bundle.riskpoolId = riskpoolId;
        bundle.capital = capital;
        bundle.createdAt = block.timestamp;
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

    function getBundle(uint256 bundleId) external view returns(Bundle memory bundle) {
        require(_bundle[bundleId].createdAt > 0, "ERROR:DIS-030:BUNDLE_DOES_NOT_EXIST");
        return _bundle[bundleId];
    }


}
