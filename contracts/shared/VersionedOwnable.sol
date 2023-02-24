// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "@openzeppelin-upgradeable/contracts/access/OwnableUpgradeable.sol";

import "./Versionable.sol";

contract VersionedOwnable is
    Versionable,
    OwnableUpgradeable
{
    // controlled initialization for controller deployment
    constructor() 
        initializer
    {
        // activation done in parent constructor
        // set msg sender as owner
        __Ownable_init();
    }


    // IMPORTANT this function needs to be implemented by each new version
    // and needs to call _activate() in derived contract implementations
    function activate(address implementation) external override virtual { 
        _activate(implementation);
    }

    // default implementation for initial deployment by proxy admin
    function activateAndSetOwner(address implementation, address newOwner)
        external
        virtual
    {
        _activateAndSetOwner(implementation, newOwner);
    }


    function _activateAndSetOwner(address implementation, address newOwner)
        internal
        virtual 
        initializer
    { 
        // ensure proper version history
        _activate(implementation);

        // initialize open zeppelin contracts
        __Ownable_init();

        // transfer to new owner
        transferOwnership(newOwner);
    }
}