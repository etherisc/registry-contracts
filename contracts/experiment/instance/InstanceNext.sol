// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {Registerable} from "../registry/Registry.sol";
import {IRegistry} from "../registry/IRegistry.sol";

import {IAccessModule, AccessModule} from "./access/Access.sol";
import {IComponentModule, ComponentModule} from "./component/Component.sol";

import {IInstanceNext} from "./IInstanceNext.sol";

contract InstanceNext is 
    IInstanceNext,
    Registerable,
    AccessModule,
    ComponentModule 
{

    constructor(
        address registry,
        address accessOwnerService,
        address componentOwnerService
    )
        AccessModule(accessOwnerService)
        ComponentModule(componentOwnerService)
    { 
        setRegistry(registry);
    }

    function getType() external view override returns(uint256 objectType) {
        return _registry.INSTANCE();
    }

    function register() external override returns(uint256 id) {
        require(address(_registry) != address(0), "ERROR:PRD-001:REGISTRY_ZERO");
        return _registry.register(address(this));
    }


}
