// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "./DemoV10.sol";

contract DemoV09 is
    DemoV10
{

    uint private _value;

    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toPart(0), toPart(9), toPart(0));
    }
}
