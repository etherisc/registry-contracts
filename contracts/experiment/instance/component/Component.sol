// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {IRegistry, IRegisterable, IRegistryLinked} from "../../registry/IRegistry.sol";
import {Registerable} from "../../registry/Registry.sol";
import {IInstanceNext} from "../IInstanceNext.sol";

import {IInstanceLinked, IComponent, IComponentContract, IComponentModule, IComponentOwnerServiceNext} from "./IComponent.sol";


contract InstanceLinked is 
    IInstanceLinked
{
    IInstanceNext internal _instance;

    constructor() {
        _instance = IInstanceNext(address(0));
    }

    function setInstance(address instance) public override {
        require(address(_instance) == address(0), "ERROR:RGL-001:INSTANCE_ALREADY_SET");
        _instance = IInstanceNext(instance);
    }

    function getInstance() external view override returns(IInstanceNext instance) {
        return _instance;
    }
}

contract ProductNext is
    Registerable,
    InstanceLinked,
    IComponentContract
{

    address private _deployer;

    constructor(address instance)
        InstanceLinked()
    {
        setInstance(instance);
        setRegistry(address(_instance.getRegistry()));
    }

    function register()
        public
        override
        // TODO restrict registery to deployer
        // TODO restrict to deployers with proper role
        returns(uint256 componentId)
    {
        require(address(_registry) != address(0), "ERROR:PRD-001:REGISTRY_ZERO");
        require(_registry.isRegistered(address(_instance)), "ERROR:PRD-002:INSTANCE_NOT_REGISTERED");

        componentId = _registry.register(address(this));
        IComponentOwnerServiceNext cos = _instance.getComponentOwnerService();
        componentId = cos.register(_instance, this);
    }

    function getType() external view override returns(uint256) {
        return _registry.PRODUCT();
    }
}

abstract contract ComponentModule is 
    IRegistryLinked,
    IComponentModule
{

    mapping(uint256 id => ComponentInfo info) private _info;
    mapping(address cAddress => uint256 id) private _idByAddress;
    uint256 [] private _ids;
    uint256 private _idNext;

    ComponentOwnerServiceNext private _ownerService;

    modifier onlyComponentOwnerService() {
        require(address(_ownerService) == msg.sender, "ERROR:CMP-001:NOT_OWNER_SERVICE");
        _;
    }

    constructor(address componentOwnerService) {
        _ownerService = ComponentOwnerServiceNext(componentOwnerService);
        _idNext = 0;
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
            id = _incAndGetNextId();

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


    function _incAndGetNextId()
        internal
        returns(uint256 nextId)
    {
        _idNext++;
        return _idNext;
    }
}


// this is actually the component owner service
contract ComponentOwnerServiceNext is
    IComponent,
    IComponentOwnerServiceNext
{

    modifier onlyComponentOwner(IComponentModule module, uint256 id) {
        IRegistry registry = module.getRegistry();
        require(
            msg.sender == registry.getOwner(id),
            "ERROR:AOS-001:NOT_COMPONENT_OWNER"
        );
        _;
    }


    function register(
        IComponentModule module, 
        IComponentContract component
    )
        external
        override
        // TODO add only product owner role
        returns(uint256 id)
    {
        require(module.getComponentId(address(component)) == 0, "ERROR_COMPONENT_ALREADY_REGISTERED");

        ComponentInfo memory info = ComponentInfo(
            0, // 0 for not registered component
            address(component),
            component.getType(),
            CState.Active
        );

        id = module.setComponentInfo(info);

        // TODO add logging
    }


    function lock(
        IComponentModule module, 
        uint256 id
    )
        external
        override
        onlyComponentOwner(module, id)
    {
        ComponentInfo memory info = module.getComponentInfo(id);
        require(info.id > 0, "ERROR_COMPONENT_UNKNOWN");
        // TODO add state change validation

        info.state = CState.Locked;
        module.setComponentInfo(info);

        // TODO add logging
    }


    function unlock(
        IComponentModule module, 
        uint256 id
    )
        external
        override
        onlyComponentOwner(module, id)
    {
        ComponentInfo memory info = module.getComponentInfo(id);
        require(info.id > 0, "ERROR_COMPONENT_UNKNOWN");
        // TODO state change validation
        info.state = CState.Active;
        module.setComponentInfo(info);

        // TODO add logging
    }

}