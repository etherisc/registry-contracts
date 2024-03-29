// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {Version, toVersion, toVersionPart} from "../shared/IVersionType.sol";
import {DemoV10} from "./DemoV10.sol";

contract DemoV11 is
    DemoV10
{

    uint private _value;

    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toVersionPart(1), toVersionPart(1), toVersionPart(0));
    }

    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activate(address implementation, address activatedBy) external virtual override { 
        // ensure proper version history
        _activate(implementation, activatedBy);

        // set main internal variables
        _value = 42;
    }


    function value() external view returns(uint) {
        return _value;
    }


    function upgradable() public virtual override view returns(string memory) {
        return "hey from upgradableDemo - Demo v1.1.0";
    }
}
