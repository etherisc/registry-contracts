// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "../shared/VersionedOwnable.sol";

contract DemoV10 is
    VersionedOwnable
{

    string private _message;

    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toPart(1), toPart(0), toPart(0));
    }


    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activateAndSetOwner(address implementation, address newOwner)
        external
        virtual override
        initializer
    {
        // ensure proper version history
        _activateAndSetOwner(implementation, newOwner);

        // set main internal variables
        _message = "special message - as initialized";
    }


    // function _initialize() internal virtual override {
    //     __Ownable_init();
    // }


    function setMessage(string memory newMessage) external onlyOwner {
        _message = newMessage;
    }

    function message() external view returns(string memory) {
        return _message;
    }

    function upgradable() public virtual view returns(string memory) {
        return "hey from upgradableDemo - DemoV1";
    }
}
