// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {Version, toVersion, toVersionPart} from "../shared/IVersionType.sol";
import {DemoV10} from "./DemoV10.sol";

contract DemoV09 is
    DemoV10
{

    uint private _value;

    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toVersionPart(0), toVersionPart(9), toVersionPart(0));
    }
}
