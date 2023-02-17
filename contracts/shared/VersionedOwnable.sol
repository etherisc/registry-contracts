// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "@openzeppelin-upgradeable/contracts/access/OwnableUpgradeable.sol";

import "./Versionable.sol";

abstract contract VersionedOwnable is
    Versionable,
    OwnableUpgradeable
{
    // controlled initialization for controller deployment
    constructor() 
        initializer
    {
        _activateAndSetOwner(address(this), msg.sender);
    }


    // IMPORTANT this function needs to be implemented by each new version
    // and needs to call _activate() in derived contract implementations
    function activate(address implementation) external override virtual { 
        _activate(implementation);
    }


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

    // // called inside initializer
    // function _initialize() internal virtual;
}