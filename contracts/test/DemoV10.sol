// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {Version, toVersion, toVersionPart} from "../shared/IVersionType.sol";

import {VersionedOwnable} from "../shared/VersionedOwnable.sol";

contract DemoV10 is
    VersionedOwnable
{

    string private _message;

    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toVersionPart(1), toVersionPart(0), toVersionPart(0));
    }


    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activateAndSetOwner(address implementation, address newOwner, address activatedBy)
        external
        virtual override
        initializer
    {
        // ensure proper version history
        _activateAndSetOwner(implementation, newOwner, activatedBy);

        // set main internal variables
        _message = "special message - as initialized";
    }


    function setMessage(string memory newMessage) external onlyOwner {
        _message = newMessage;
    }

    function message() external view returns(string memory) {
        return _message;
    }

    function upgradable() public virtual view returns(string memory) {
        return "hey from upgradableDemo - Demo v1.0.0";
    }
}
