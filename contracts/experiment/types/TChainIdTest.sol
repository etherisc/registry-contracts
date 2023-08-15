// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {TChainId, toTChainId} from "./TChainId.sol";

contract TChainIdTest {
    function toChainId(uint256 id) external pure returns(TChainId) {
        return toTChainId(id);
    }

    function toInt(TChainId id) external pure returns(uint256) {
        return id.toInt();
    }

    function chainId() external view returns(TChainId) {
        return toTChainId(block.chainid);
    }

    function isSameChain(TChainId a, TChainId b) external pure returns(bool) {
        return a == b;
    }
}