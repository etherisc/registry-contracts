// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {OwnableUpgradeable} from "@openzeppelin-upgradeable/contracts/access/OwnableUpgradeable.sol";

// test contract to check storage layout of OwnableUpgradeable
// openzeppelin's OwnableUpgradeable creates two __gap slots as shown below
// {
//     "label": "__gap",
//     "offset": 0,
//     "slot": "1",
//     "type": "t_array(t_uint256)7325f_storage"
// },

contract TestUpgradableV01 is
    OwnableUpgradeable
{
    uint8 private _one;

    constructor() {
        _one = 1;
    }

    function getOne() external view returns(uint8 value) { return _one; }
}