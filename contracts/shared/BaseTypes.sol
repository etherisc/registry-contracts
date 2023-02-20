// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "./IBaseTypes.sol";

// // restriction: uint<n> n needs to be different for each type to support function overloading
// type VersionPart is uint16;
// type Version is uint48; // to concatenate major,minor,patch version parts

// type ChainId is bytes3;
// type Blocknumber is uint32;
// type Timestamp is uint40;

// type Amount is uint128;


contract BaseTypes is IBaseTypes {

    function intToBytes(uint256 x, uint8 shift) public override pure returns(bytes memory) {
        return abi.encodePacked(uint16(x << shift));
    }

    function toInt(VersionPart x) public override pure returns(uint) { return VersionPart.unwrap(x); }
    function toInt(Version x) public override pure returns(uint) { return Version.unwrap(x); }
    function toInt(Blocknumber x) public override pure returns(uint) { return Blocknumber.unwrap(x); }
    function toInt(Timestamp x) public override pure returns(uint) { return Timestamp.unwrap(x); }
    function toInt(Amount x) public override pure returns(uint) { return Amount.unwrap(x); }
    function toInt(ChainId x) public override pure returns(uint) { return uint(uint24(ChainId.unwrap(x))); }

    function toChainId(uint256 x) public override pure returns(ChainId) { return ChainId.wrap(bytes3(abi.encodePacked(uint24(x)))); }

    function blockTimestamp() public override view returns(Timestamp) {
        return Timestamp.wrap(uint32(block.timestamp));
    }

    function blockNumber() public override view returns(Blocknumber) {
        return Blocknumber.wrap(uint32(block.number));
    }
}