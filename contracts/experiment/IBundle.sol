// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {IChainNft, NftId, toNftId} from "../registry/IChainNft.sol";

interface IBundle {

    enum BundleState {
        Undefined,
        Active,
        Locked,
        Closed,
        Burned
    }

    struct Bundle {
        NftId id;
        uint256 riskpoolId;
        uint256 tokenId;
        BundleState state;
        bytes filter; // required conditions for applications to be considered for collateralization by this bundle
        uint256 capital; // net investment capital amount (<= balance)
        uint256 lockedCapital; // capital amount linked to collateralizaion of non-closed policies (<= capital)
        uint256 balance; // total amount of funds: net investment capital + net premiums - payouts
        uint256 createdAt;
        uint256 updatedAt;
    }
}
