// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "./ObjectRegistryV1.sol";

contract ObjectRegistryV2 is
    ObjectRegistryV1
{

    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toPart(0), toPart(0), toPart(2));
    }

    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activate(address implementation) external override virtual { 
        _activate(implementation);
    }
}