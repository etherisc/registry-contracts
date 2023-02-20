// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

// restriction: uint<n> n needs to be different for each type to support function overloading
type VersionPart is uint16;
type Version is uint48; // to concatenate major,minor,patch version parts

type ChainId is bytes3;
type Blocknumber is uint32;
type Timestamp is uint40;

type Amount is uint128;

interface IBaseTypes {

    function intToBytes(uint256 x, uint8 shift) external pure returns(bytes memory);

    function toInt(VersionPart x) external pure returns(uint);
    function toInt(Version x) external pure returns(uint);
    function toInt(Blocknumber x) external pure returns(uint);
    function toInt(Timestamp x) external pure returns(uint);
    function toInt(Amount x) external pure returns(uint);
    function toInt(ChainId x) external pure returns(uint);

    function toChainId(uint256 x) external pure returns(ChainId);

    function blockTimestamp() external view returns(Timestamp);
    function blockNumber() external view returns(Blocknumber);
}