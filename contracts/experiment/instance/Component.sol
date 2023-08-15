// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {IComponent, IComponentContract, IComponentModule, IComponentOwnerServiceNext} from "./IComponent.sol";
import {IInstanceNext} from "./IInstanceNext.sol";


contract ProductNext is IComponentContract {

    CType private _type;
    IInstanceNext private _instance;

    constructor(IInstanceNext instance) {
        _type = CType.Product;
        _instance = instance;
    }

    function register()
        external
        override
        // TODO restrict registery to deployer
        // TODO restrict to deployers with proper role
        returns(uint256 componentId)
    {
        IComponentOwnerServiceNext cos = _instance.getComponentOwnerService();
        componentId = cos.register(_instance, this);
    }

    function getId() external view returns(uint256 id) {
        return _instance.getComponentId(address(this));
    }

    function getType() external view returns(CType cType) {
        return _type;
    }

    function getInstanceAddress() external view returns(address) {
        return address(_instance);
    }
}

contract ComponentModule is IComponentModule {

    mapping(uint256 id => ComponentInfo info) private _info;
    mapping(address cAddress => uint256 id) private _idByAddress;
    uint256 [] private _ids;
    uint256 private _idNext;

    ComponentOwnerServiceNext private _componentOwnerServiceNext;

    modifier onlyController() {
        require(address(_componentOwnerServiceNext) == msg.sender, "ERROR:CMP-001:NOT_ComponentOwnerServiceNext");
        _;
    }

    constructor(address componentOwnerService) {
        _componentOwnerServiceNext = ComponentOwnerServiceNext(componentOwnerService);
        _idNext = 0;
    }

    function getComponentOwnerService()
        external
        override
        view
        returns(IComponentOwnerServiceNext)
    {
        return _componentOwnerServiceNext;
    }

    function setComponentInfo(ComponentInfo memory info)
        external
        onlyController
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
        // TODO add owner of this product
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
        // TODO add owner of this product
    {
        ComponentInfo memory info = module.getComponentInfo(id);
        require(info.id > 0, "ERROR_COMPONENT_UNKNOWN");
        // TODO state change validation
        info.state = CState.Active;
        module.setComponentInfo(info);

        // TODO add logging
    }

}