// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;


import {IOwnable, IRegistryLinked, IRegisterable} from "../../registry/IRegistry.sol";
import {IInstanceNext} from "../IInstanceNext.sol";

interface IComponent {

    enum CState {
        Undefined,
        Active,
        Locked
    }

    struct ComponentInfo {
        uint256 id;
        address cAddress;
        uint256 cType;
        CState state;
    }
}


interface IInstanceLinked {
    function setInstance(address instance) external;
    function getInstance() external view returns(IInstanceNext instance);
}


interface IComponentContract is
    IRegisterable,
    IInstanceLinked,
    IComponent
{ }


interface IComponentOwnerServiceNext {

    function register(
        IComponentModule module, 
        IComponentContract component
    )
        external
        returns(uint256 id);
    
    function lock(
        IComponentModule module, 
        uint256 id
    )
        external;
    
    function unlock(
        IComponentModule module, 
        uint256 id
    )
        external;
}


interface IComponentModule is
    IOwnable,
    IRegistryLinked,
    IComponent
{

    function setComponentInfo(ComponentInfo memory info)
        external
        returns(uint256 componentId);

    function getComponentInfo(uint256 id)
        external
        view
        returns(ComponentInfo memory info);

    function getComponentOwner(uint256 id)
        external
        view
        returns(address owner);

    function getComponentId(address componentAddress)
        external
        view
        returns(uint256 id);

    function getComponentId(uint256 idx)
        external
        view
        returns(uint256 id);

    function components()
        external
        view
        returns(uint256 numberOfCompnents);

    function getComponentOwnerService()
        external
        view
        returns(IComponentOwnerServiceNext);
}