// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {Version, toVersion, toVersionPart} from "../shared/IVersionType.sol";
import {DemoV11} from "./DemoV11.sol";

contract DemoV111 is
    DemoV11
{

    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toVersionPart(1), toVersionPart(1), toVersionPart(1));
    }

    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activate(address implementation, address activatedBy) external virtual override { 
        // ensure proper version history
        _activate(implementation, activatedBy);
    }


    function ping() public pure returns(string memory) {
        return "pong";
    }
}
