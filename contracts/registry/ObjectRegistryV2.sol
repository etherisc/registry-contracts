// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "./ObjectRegistryV1.sol";

contract ObjectRegistryV2 is
    ObjectRegistryV1
{

    // IMPORTANT initilizeer for upgradable logig
    function initialize() public virtual override initializer {
        require(version() == 1, "PREVIOUS_VERSION_INVALID");
        // version handling
        _increaseVersion();
    }
}
