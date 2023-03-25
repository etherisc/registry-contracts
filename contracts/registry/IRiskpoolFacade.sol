// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

/*
 *  @dev needs to be in sync with definition in DepegRiskpool
 */

import {IStaking} from "../staking/IStaking.sol";

interface IRiskpoolFacade {

    function setStakingAddress(address staking) external;

    function activeBundles() external view returns(uint256);
    function getActiveBundleId(uint256 idx) external view returns(uint256 bundleId);
    function getStaking() external view returns(IStaking staking);
}