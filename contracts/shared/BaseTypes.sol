// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

// restriction: uint<n> n needs to be different for each type to support function overloading
type VersionPart is uint16;
type Version is uint48; // to concatenate major,minor,patch version parts

type Blocknumber is uint32;
type Timestamp is uint40;

type NumericId is uint64;
type Amount is uint128;


contract BaseTypes {

    function toInt(VersionPart x) public pure returns(uint) { return VersionPart.unwrap(x); }
    function toInt(Version x) public pure returns(uint) { return Version.unwrap(x); }
    function toInt(NumericId x) public pure returns(uint) { return NumericId.unwrap(x); }
    function toInt(Amount x) public pure returns(uint) { return Amount.unwrap(x); }
    function toInt(Timestamp x) public pure returns(uint) { return Timestamp.unwrap(x); }
    function toInt(Blocknumber x) public pure returns(uint) { return Blocknumber.unwrap(x); }

    function blockTimestamp() public view returns(Timestamp) {
        return Timestamp.wrap(uint32(block.timestamp));
    }

    function blockNumber() public view returns(Blocknumber) {
        return Blocknumber.wrap(uint32(block.number));
    }
}