// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "./DemoV1.sol";

contract DemoV2 is
    DemoV1
{

    uint private _value;

    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toPart(1), toPart(1), toPart(0));
    }

    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activate(address implementation) external override virtual { 
        _activate(implementation);
        _value = 42;
    }


    function theValue() external view returns(uint) {
        return _value;
    }

    function upgradableDemo() public virtual override view returns(string memory) {
        return "hey from upgradableDemo - DemoV2";
    }
}
