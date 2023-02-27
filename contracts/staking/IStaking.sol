// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "../shared/IBaseTypes.sol";
import "../shared/UFixedMath.sol";
import "../registry/IChainRegistry.sol";

interface IStaking {

    //--- state changing functions ------------------//

    function setStakingRate(ChainId chain, address token, UFixed stakingRate) external;    
    function setRewardRate(UFixed rewardRate) external;
    function increaseRewardReserves(Amount dips) external;

    // TODO implement
    // function stake(NftId target, Amount dips) external;
    // function unstake(NftId target, Amount dips) external;  
    // function unstakeAndClaimRewards(NftId target) external;
    // function claimRewards(NftId target) external;

    //--- view and pure functions ------------------//

    function stakingRate(ChainId chain, address token) external returns(UFixed stakingRate);
    function rewardRate() external returns(UFixed rewardRate);
    function rewardReserves() external returns(Amount dips);

}
