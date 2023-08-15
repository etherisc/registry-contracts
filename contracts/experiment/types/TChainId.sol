// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

// bytes5 allows for chain ids up to 13 digits
type TChainId is bytes5;

// type bindings
using {
    eqTChainId as ==,
    neTChainId as !=,
    TChainIdLib.toInt
} for TChainId global;

// general pure free functions
function toTChainId(uint256 chainId) pure returns(TChainId) { return TChainId.wrap(bytes5(uint40(chainId))); }

// pure free functions for operators
function eqTChainId(TChainId a, TChainId b) pure returns(bool isSame) { return TChainId.unwrap(a) == TChainId.unwrap(b); }
function neTChainId(TChainId a, TChainId b) pure returns(bool isDifferent) { return TChainId.unwrap(a) != TChainId.unwrap(b); }

// library functions that operate on user defined type
library TChainIdLib {
    function toInt(TChainId chainId) internal pure returns(uint256) { return uint256(uint40(TChainId.unwrap(chainId))); }
}
