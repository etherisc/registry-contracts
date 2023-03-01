// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "../shared/IBaseTypes.sol";
import "../shared/UFixedMath.sol";
import "../registry/IChainRegistry.sol";


interface IStaking {

    struct StakeInfo {
        NftId id;
        NftId target;
        uint256 stakeBalance;
        uint256 rewardBalance;
        Timestamp createdAt;
        Timestamp updatedAt;
    }

    event LogStakingRewardReservesIncreased(address user, uint256 amount, uint256 newBalance);

    event LogStakingRewardRateSet(UFixed oldRewardRate, UFixed newRewardRate);
    event LogStakingStakingRateSet(ChainId chain, address token, UFixed oldStakingRate, UFixed newStakingRate);

    event LogStakingNewStake(NftId target, address user, NftId id);
    event LogStakingStaked(NftId target, address user, NftId id, uint256 amount, uint256 newBalance);
    event LogStakingUnstaked(NftId target, address user, NftId id, uint256 amount, uint256 newBalance);

    event LogStakingRewardsUpdated(NftId target, address user, NftId id, uint256 amount, uint256 newBalance);
    event LogStakingRewardsClaimed(NftId target, address user, NftId id, uint256 amount, uint256 newBalance);

    //--- state changing functions ------------------//

    function setStakingRate(ChainId chain, address token, UFixed stakingRate) external;    
    function setRewardRate(UFixed rewardRate) external;

    function refillRewardReserves(uint256 dipAmount) external;
    function withdrawRewardReserves(uint256 dipAmount) external;

    function createStake(NftId target, uint256 dipAmount) external returns(NftId id);
    function stake(NftId id, uint256 dipAmount) external;
    function unstake(NftId id, uint256 dipAmount) external;  
    function unstakeAndClaimRewards(NftId id) external;
    function claimRewards(NftId id) external;

    //--- view and pure functions ------------------//

    function getInfo(NftId stake) external view returns(StakeInfo memory info);

    function isStakingSupported(NftId target) external view returns(bool isSupported);
    function isStakingSupportedForType(ObjectType targetType) external view returns(bool isSupported);

    function stakingRate(ChainId chain, address token) external view returns(UFixed stakingRate);
    function rewardRate() external view returns(UFixed rewardRate);
    function rewardReserves() external view returns(uint256 dipAmount);
    function getStakingWallet() external view returns(address stakingWallet);

    function toRate(uint256 value, int8 exp) external pure returns(UFixed);
    function rateDecimals() external pure returns(uint256 decimals);
}
