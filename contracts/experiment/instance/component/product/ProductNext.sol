// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {ProductBase} from "./ProductBase.sol";


contract ProductNext is ProductBase {

    constructor(address instance) ProductBase(instance) { }

}