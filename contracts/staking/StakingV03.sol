// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {Version, toVersion, toVersionPart} from "../shared/IVersionType.sol";
import {Timestamp, blockTimestamp, toTimestamp, zeroTimestamp} from "../shared/IBaseTypes.sol";
import {UFixed} from "../shared/UFixedMath.sol";

import {IChainRegistry, ObjectType} from "../registry/ChainRegistryV01.sol";
import {NftId} from "../registry/IChainNft.sol";

import {StakingV02} from "./StakingV02.sol";

contract StakingV03 is
    StakingV02
{

    struct RewardInfo {
        UFixed rewardRate;
        Timestamp createdAt;
        Timestamp updatedAt;
    }

    mapping(NftId target => RewardInfo rewardRate) internal _targetRewardRate;


    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version()
        public
        virtual override
        pure
        returns(Version)
    {
        return toVersion(
            toVersionPart(1),
            toVersionPart(1),
            toVersionPart(0));
    }


    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activate(address implementation, address activatedBy)
        external 
        virtual override
    { 
        // keep track of version history
        // do some upgrade checks
        _activate(implementation, activatedBy);

        // upgrade version
        _version = version();
    }


    function setTargetRewardRate(NftId target, UFixed newRewardRate)
        external
        virtual
    {
        require(_registry.exists(target), "ERROR:STK-310:TARGET_NOT_EXISTING");
        require(newRewardRate <= _rewardRateMax, "ERROR:STK-311:REWARD_EXCEEDS_MAX_VALUE");

        RewardInfo storage info = _targetRewardRate[target];        
        UFixed oldRewardRate = info.rewardRate;

        info.rewardRate = newRewardRate;
        info.updatedAt = blockTimestamp();

        if(info.createdAt == zeroTimestamp()) {
            info.createdAt = blockTimestamp();
            oldRewardRate = _rewardRate;
        }

        emit LogTargetRewardRateSet(msg.sender, target, oldRewardRate, newRewardRate);
    }


    function updateRewards(NftId stakeId)
        external
        virtual
    {
        // input validation (stake needs to exist)
        StakeInfo storage info = _info[stakeId];
        require(info.createdAt > zeroTimestamp(), "ERROR:STK-320:STAKE_NOT_EXISTING");

        _updateRewards(info);
    }


    function createStake(NftId target, uint256 dipAmount)
        external
        virtual override
        returns(NftId stakeId)
    {
        // no validation here, validation is done via calling stake() at the end
        address user = msg.sender;
        stakeId = _registry.registerStake(target, user);

        StakeInfo storage info = _info[stakeId];
        info.id = stakeId;
        info.target = target;
        info.stakeBalance = 0;
        info.rewardBalance = 0;
        info.createdAt = blockTimestamp();
        info.lockedUntil = calculateLockingUntil(target);
        info.version = version();

        stake(stakeId, dipAmount);

        emit LogStakingNewStakeCreated(target, user, stakeId);
    }


    function getTargetRewardRate(NftId target)
        public
        virtual
        view
        returns(UFixed rewardRate)
    {
        RewardInfo memory info = _targetRewardRate[target];

        if(info.createdAt > zeroTimestamp()) {
            return info.rewardRate;
        }

        // fallback if no target specific rate is defined
        return _rewardRate;
    }


    function calculateLockingUntil(NftId target)
        public
        virtual
        view
        returns(Timestamp lockedUntil)
    {
        IChainRegistry.NftInfo memory info = _registry.getNftInfo(target);

        if(info.objectType == _registryConstant.BUNDLE()) {
            (,,,,, uint256 expiryAt) = _registry.decodeBundleData(target);
            return toTimestamp(expiryAt);
        }

        return zeroTimestamp();
    }


    function calculateRewardsIncrement(StakeInfo memory stake)
        public 
        virtual override
        view
        returns(uint256 rewardsAmount)
    {
        /* solhint-disable not-rely-on-time */
        require(block.timestamp >= toInt(stake.updatedAt), "ERROR:STK-200:UPDATED_AT_IN_THE_FUTURE");
        uint256 timeSinceLastUpdate = block.timestamp - toInt(stake.updatedAt);
        /* solhint-enable not-rely-on-time */

        // TODO potentially reduce time depending on the time when the bundle has been closed

        UFixed rewardRate = getTargetRewardRate(stake.target);
        rewardsAmount = calculateRewards(stake.stakeBalance, timeSinceLastUpdate, rewardRate);
    }


    function calculateRewards(
        uint256 amount,
        uint256 duration,
        UFixed rate
    ) 
        public 
        virtual
        view
        returns(uint256 rewardAmount) 
    {
        UFixed yearFraction = itof(duration) / itof(YEAR_DURATION);
        UFixed rewardDuration = rate * yearFraction;
        rewardAmount = ftoi(itof(amount) * rewardDuration);
    }

}
