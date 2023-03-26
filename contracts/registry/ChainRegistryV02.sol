// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {Version, toVersion, toVersionPart} from "../shared/IVersionType.sol";
import {IVersionable} from "../shared/IVersionable.sol";
import {Versionable} from "../shared/Versionable.sol";
import {VersionedOwnable} from "../shared/VersionedOwnable.sol";

import {ChainId} from "../shared/IBaseTypes.sol";
import {ChainRegistryV01} from "./ChainRegistryV01.sol";

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
    function version()
        public 
        virtual override
        pure
        returns(Version)
    {
        return toVersion(
            toVersionPart(0),
            toVersionPart(1),
            toVersionPart(1));
    }

    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activate(address implementation, address activatedBy)
        external 
        virtual override(IVersionable, VersionedOwnable)
    { 
        // keep track of version history
        // do some upgrade checks
        _activate(implementation, activatedBy);

        // upgrade version
        _version = version();
    }
}