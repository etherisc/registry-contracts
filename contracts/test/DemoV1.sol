// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "../shared/VersionedOwnable.sol";

contract DemoV1 is
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
    function activate(address implementation) external override virtual { 
        _activate(implementation);
        _message = "special message - as initialized";
    }

    function setSpecialMessage(string memory message) external onlyOwner {
        _message = message;
    }

    function specialMessage() external view returns(string memory) {
        return _message;
    }

    function nonUpgradableDemo1() external view returns(string memory) {
        return "hi from nonUpgradableDemo1()";
    }

    function upgradableDemo() public virtual view returns(string memory) {
        return "hey from upgradableDemo - DemoV1";
    }
}
