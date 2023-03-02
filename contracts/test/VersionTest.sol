// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "../shared/VersionType.sol";

contract VersionTest {

    function gt(Version a, Version b) external pure returns(bool) {
        return a > b;
    }

    function gte(Version a, Version b) external pure returns(bool) {
        return a >= b;
    }

    function eq(Version a, Version b) external pure returns(bool) {
        return a == b;
    }

    function tp(uint16 p) external pure returns(VersionPart) {
        return toVersionPart(p);
    }

    function tv(VersionPart major, VersionPart minor, VersionPart patch) external pure returns(Version){
        return toVersion(major, minor, patch);
    }
}