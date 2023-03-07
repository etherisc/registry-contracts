// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "../shared/IBaseTypes.sol";
import "../shared/UFixedMath.sol";

import "../registry/ChainRegistryV01.sol";
import "../registry/IChainRegistry.sol";


interface IStaking {

    struct StakeInfo {
        NftId id;
        NftId target;
        uint256 stakeBalance;
        uint256 rewardBalance;
        Timestamp createdAt;
        Timestamp updatedAt;
        Version version;
    }

    event LogStakingRewardReservesIncreased(address user, uint256 amount, uint256 newBalance);
    event LogStakingRewardReservesDecreased(address user, uint256 amount, uint256 newBalance);

    event LogStakingRewardRateSet(address user, UFixed oldRewardRate, UFixed newRewardRate);
    event LogStakingStakingRateSet(address user, ChainId chain, address token, UFixed oldStakingRate, UFixed newStakingRate);

    event LogStakingNewStake(NftId target, address user, NftId id);
    event LogStakingStaked(NftId target, address user, NftId id, uint256 amount, uint256 newBalance);
    event LogStakingUnstaked(NftId target, address user, NftId id, uint256 amount, uint256 newBalance);

    event LogStakingRewardsUpdated(NftId id, uint256 amount, uint256 newBalance);
    event LogStakingRewardsClaimed(NftId id, uint256 amount, uint256 newBalance);

    //--- state changing functions ------------------//

    function refillRewardReserves(uint256 dipAmount) external;
    function withdrawRewardReserves(uint256 dipAmount) external;

    function setRewardRate(UFixed rewardRate) external;
    function setStakingRate(ChainId chain, address token, UFixed stakingRate) external;    

    function createStake(NftId target, uint256 dipAmount) external returns(NftId id);
    function stake(NftId id, uint256 dipAmount) external;
    function unstake(NftId id, uint256 dipAmount) external;  
    function unstakeAndClaimRewards(NftId id) external;
    function claimRewards(NftId id) external;

    //--- view and pure functions ------------------//

    function getRegistry() external view returns(ChainRegistryV01);

    function rewardRate() external view returns(UFixed rewardRate);
    function rewardBalance() external view returns(uint256 dipAmount);
    function rewardReserves() external view returns(uint256 dipAmount);
    function stakingRate(ChainId chain, address token) external view returns(UFixed stakingRate);
    function getStakingWallet() external view returns(address stakingWallet);
    function getDip() external view returns(IERC20Metadata);

    function isStakeOwner(NftId id, address user) external view returns(bool isOwner);
    function getInfo(NftId id) external view returns(StakeInfo memory info);

    function stakes(NftId target) external view returns(uint256 dipAmount);
    function capitalSupport(NftId target) external view returns(uint256 capitalAmount);

    function isStakingSupportedForType(ObjectType targetType) external view returns(bool isSupported);
    function isStakingSupported(NftId target) external view returns(bool isSupported);
    function isUnstakingSupported(NftId target) external view returns(bool isSupported);

    function calculateRewardsIncrement(StakeInfo memory stakeInfo) external view returns(uint256 rewardsAmount);
    function calculateRewards(uint256 amount, uint256 duration) external view returns(uint256 rewardAmount);

    function calculateRequiredStaking(ChainId chain, address token, uint256 tokenAmount) external view returns(uint256 dipAmount);
    function calculateCapitalSupport(ChainId chain, address token, uint256 dipAmount) external view returns(uint256 tokenAmount);

    function toChain(uint256 chainId) external pure returns(ChainId);

    function toRate(uint256 value, int8 exp) external pure returns(UFixed);
    function rateDecimals() external pure returns(uint256 decimals);

    //--- view and pure functions (target type specific) ------------------//

    function getBundleInfo(NftId bundle)
        external
        view
        returns(
            bytes32 instanceId,
            uint256 riskpoolId,
            uint256 bundleId,
            address token,
            string memory displayName,
            IInstanceServiceFacade.BundleState bundleState,
            Timestamp expiryAt,
            bool stakingSupported,
            bool unstakingSupported,
            uint256 stakeBalance
        );
}
