// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

// restriction: uint<n> n needs to be different for each type to support function overloading
type ChainId is bytes3;
type Blocknumber is uint32;
type Timestamp is uint40;

type Amount is uint128;

function toAmount(uint256 a) pure returns(Amount) { return Amount.wrap(uint128(a)); }

interface IBaseTypes {

    function intToBytes(uint256 x, uint8 shift) external pure returns(bytes memory);

    function toInt(Blocknumber x) external pure returns(uint);
    function toInt(Timestamp x) external pure returns(uint);
    function toInt(Amount x) external pure returns(uint);
    function toInt(ChainId x) external pure returns(uint);

    function toChainId(uint256 x) external pure returns(ChainId);

    function blockTimestamp() external view returns(Timestamp);
    function blockNumber() external view returns(Blocknumber);
}