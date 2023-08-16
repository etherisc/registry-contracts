// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {IRegisterable} from "../registry/IRegistry.sol";
import {IAccessModule} from "./access/IAccess.sol";
import {IComponentModule} from "./component/IComponent.sol";


interface IInstanceNext is
    IRegisterable,
    IAccessModule,
    IComponentModule
{ }

