// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "../shared/IBaseTypes.sol";
import "../shared/UFixedMath.sol";
import "../registry/IChainRegistry.sol";


interface IStaking {

    struct StakeInfo {
        NftId target;
        uint256 stakeBalance;
        uint256 rewardBalance;
        Timestamp createdAt;
        Timestamp updatedAt;
    }

    //--- state changing functions ------------------//

    function setStakingRate(ChainId chain, address token, UFixed stakingRate) external;    
    function setRewardRate(UFixed rewardRate) external;

    function refillRewardReserves(uint256 dipAmount) external;
    function withdrawRewardReserves(uint256 dipAmount) external;

    function stake(NftId target, uint256 dipAmount) external returns(NftId stakeId);

    // TODO implement
    // function unstake(NftId target, Amount dips) external;  
    // function unstakeAndClaimRewards(NftId target) external;
    // function claimRewards(NftId target) external;

    //--- view and pure functions ------------------//

    function hasInfo(NftId target, address user) external view returns(bool hasInfos);
    function getInfo(NftId target, address user) external view returns(StakeInfo memory info);
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
