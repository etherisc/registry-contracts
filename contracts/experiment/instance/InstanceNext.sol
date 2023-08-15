// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {IInstanceNext} from "./IInstanceNext.sol";
import {ComponentModule, IComponent} from "./Component.sol";

contract InstanceNext is 
    IInstanceNext,
    ComponentModule 
{


    constructor(
        address componentControllerAddress
    )
        ComponentModule(componentControllerAddress)
    { }


}
