// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "../shared/IBaseTypes.sol";
import "../shared/IUFixedMath.sol";
import "../registry/IChainRegistry.sol";

interface IStaking {

    //--- state changing functions ------------------//

    function setStakingRate(ChainId chain, address token, UFixed stakingRate) external;    
    function setRewardRate(UFixed rewardRate) external;
    function increaseRewardReserves(Amount dips) external;

    function stake(NftId target, Amount dips) external;
    function unstake(NftId target, Amount dips) external;  
    function unstakeAndClaimRewards(NftId target) external;
    function claimRewards(NftId target) external;

    //--- view and pure functions ------------------//

}
