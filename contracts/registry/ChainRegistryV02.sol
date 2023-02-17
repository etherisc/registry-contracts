// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "./ChainRegistryV01.sol";

contract ChainRegistryV02 is
    ChainRegistryV01
{

    struct InstanceInfo {
        ChainId chain;
        bytes32 instanceId;
        address instanceRegistry;
    }

    struct ComponentInfo {
        bytes32 instanceId;
        uint256 componentId;
    }

    struct BundleInfo {
        bytes32 instanceId;
        uint256 componentId;
        uint256 bundleId;
    }

    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toPart(0), toPart(1), toPart(1));
    }

    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activate(address implementation) external override virtual { 
        // keep track of version history
        // do some upgrade checks
        _activate(implementation);

        // upgrade version
        _version = version();
    }
}