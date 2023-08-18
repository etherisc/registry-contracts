// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {IRegistry, IRegisterable, IRegistryLinked} from "../../registry/IRegistry.sol";
import {Registerable} from "../../registry/Registry.sol";
import {IInstanceNext} from "../IInstanceNext.sol";

import {IAccessModule} from "../access/IAccess.sol";
import {IComponent, IComponentContract, IComponentModule, IComponentOwnerServiceNext} from "./IComponent.sol";


abstract contract ComponentModule is 
    IRegistryLinked,
    IComponentModule
{

    mapping(uint256 id => ComponentInfo info) private _info;
    mapping(address cAddress => uint256 id) private _idByAddress;
    uint256 [] private _ids;

    mapping(uint256 cType => bytes32 role) private _componentOwnerRole;

    IComponentOwnerServiceNext private _ownerService;

    modifier onlyComponentOwnerService() {
        require(address(_ownerService) == msg.sender, "ERROR:CMP-001:NOT_OWNER_SERVICE");
        _;
    }

    constructor(address componentOwnerService) {
        _ownerService = ComponentOwnerServiceNext(componentOwnerService);
    }

    function getComponentOwnerService()
        external
        override
        view
        returns(IComponentOwnerServiceNext)
    {
        return _ownerService;
    }

    function setComponentInfo(ComponentInfo memory info)
        external
        onlyComponentOwnerService
        returns(uint256 id)
    {
        // check if new component
        id = _idByAddress[info.cAddress];

        if(id == 0) {
            id = this.getRegistry().register(info.cAddress);

            _idByAddress[info.cAddress] = id;
            _ids.push(id);

            info.id = id;
        }

        _info[id] = info;

    }

    function getComponentInfo(uint256 id)
        external
        override
        view
        returns(ComponentInfo memory)
    {
        return _info[id];
    }

    function getComponentOwner(uint256 id)
        external
        view
        returns(address owner)
    {

    }

    function getComponentId(address componentAddress)
        external
        view
        returns(uint256 id)
    {
        return _idByAddress[componentAddress];
    }


    function getComponentId(uint256 idx)
        external
        override
        view
        returns(uint256 id)
    {
        return _ids[idx];
    }


    function components()
        external
        override
        view
        returns(uint256 numberOfCompnents)
    {
        return _ids.length;
    }
}


// this is actually the component owner service
contract ComponentOwnerServiceNext is
    IComponent,
    IComponentOwnerServiceNext
{

    modifier onlyComponentOwner(IComponentContract component) {
        IRegistry registry = component.getRegistry();
        require(
            msg.sender == registry.getOwner(component.getNftId()),
            "ERROR:AOS-001:NOT_COMPONENT_OWNER"
        );
        _;
    }


    modifier onlyComponentOwnerRole(IComponentContract component) {
        IInstanceNext instance = component.getInstance();
        // TODO add set/getComponentOwnerRole to IComonentModule
        bytes32 typeRole = instance.getComponentTypeRole(component.getType());
        require(
            instance.hasRole(typeRole, msg.sender),
            "ERROR:AOS-002:COMPONENT_ROLE_MISSING"
        );
        _;
    }


    function register(IComponentContract component)
        external
        override
        onlyComponentOwnerRole(component)
        returns(uint256 id)
    {
        IInstanceNext instance = component.getInstance();
        require(instance.getComponentId(address(component)) == 0, "ERROR_COMPONENT_ALREADY_REGISTERED");

        ComponentInfo memory info = ComponentInfo(
            0, // 0 for not registered component
            address(component),
            component.getType(),
            CState.Active
        );

        id = instance.setComponentInfo(info);

        
    }


    function lock(IComponentContract component)
        external
        override
        onlyComponentOwner(component)
    {
        IInstanceNext instance = component.getInstance();
        ComponentInfo memory info = instance.getComponentInfo(component.getNftId());
        require(info.id > 0, "ERROR_COMPONENT_UNKNOWN");
        // TODO add state change validation

        info.state = CState.Locked;
        instance.setComponentInfo(info);

        
    }


    function unlock(IComponentContract component)
        external
        override
        onlyComponentOwner(component)
    {
        IInstanceNext instance = component.getInstance();
        ComponentInfo memory info = instance.getComponentInfo(component.getNftId());
        require(info.id > 0, "ERROR_COMPONENT_UNKNOWN");
        // TODO state change validation

        info.state = CState.Active;
        instance.setComponentInfo(info);

        
    }

}