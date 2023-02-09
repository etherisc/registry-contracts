// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "@openzeppelin-upgradeable/contracts/access/OwnableUpgradeable.sol";

import "./Versionable.sol";

contract VersionedOwnable is
    Versionable,
    OwnableUpgradeable
{
    // controlled initialization for controller deployment
    constructor() {
        _activateFromConstructor();
        initialize();
    }

    // IMPORTANT this function needs to be implemented by each new version
    // and needs to call _activate() in derived contract implementations
    function activate(address implementation) external override virtual { 
        _activate(implementation);
        initialize();
    }

    function activateAndSetOwner(address implementation, address newOwner)
        external
        virtual 
    { 
        _activate(implementation);
        initialize();
        transferOwnership(newOwner);
    }

    function initialize() internal initializer {
        __Ownable_init();
    }
}