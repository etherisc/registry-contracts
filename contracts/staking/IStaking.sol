// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "../shared/IBaseTypes.sol";
import "../shared/IUFixedMath.sol";

interface IStaking {

    function setStakingRate(ChainId chain, address token, UFixed stakingRate) external;    
    function setRewardRate(UFixed rewardRate) external;
    function increaseRewardReserves(Amount dips) external;

    function stake(uint256 targetId, Amount dips) external;
    function unstake(uint256 targetId, Amount dips) external;  
    function unstakeAndClaimRewards(uint256 targetId) external;
    function claimRewards(uint256 targetId) external;
}
