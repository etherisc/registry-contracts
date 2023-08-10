// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {Version, toVersion, toVersionPart} from "../shared/IVersionType.sol";
import {Timestamp, blockTimestamp, toTimestamp, zeroTimestamp} from "../shared/IBaseTypes.sol";
import {UFixed} from "../shared/UFixedMath.sol";

import {IChainRegistry, ObjectType} from "../registry/ChainRegistryV01.sol";
import {NftId} from "../registry/IChainNft.sol";

import {StakingV02} from "./StakingV02.sol";
import {StakingMessageHelper} from "./StakingMessageHelper.sol";


contract StakingV03 is
    StakingV02
{

    struct RewardInfo {
        UFixed rewardRate;
        Timestamp createdAt;
        Timestamp updatedAt;
    }

    StakingMessageHelper private _messageHelper;

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


    function setMessageHelper(address stakingMessageHelper)
        external
        onlyOwner
    {
        _messageHelper = StakingMessageHelper(stakingMessageHelper);
    }


    function setTargetRewardRate(NftId target, UFixed newRewardRate)
        external
        virtual
        onlyOwner
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
        onlyOwner
    {
        // input validation (stake needs to exist)
        StakeInfo storage info = _info[stakeId];
        require(info.createdAt > zeroTimestamp(), "ERROR:STK-320:STAKE_NOT_EXISTING");

        _updateRewards(info);
    }


    function createStakeWithSignature(
        address owner,
        NftId target, 
        uint256 dipAmount,
        bytes32 signatureId,
        bytes calldata signature
    )
        external
        virtual
        override
        returns(NftId stakeId)
    {
        _messageHelper.processStakeSignature(
            owner,
            target,
            dipAmount,
            signatureId,
            signature);

        return _createStake(owner, target, dipAmount);
    }


    function createStake(NftId target, uint256 dipAmount)
        external
        virtual override
        returns(NftId stakeId)
    {
        return _createStake(msg.sender, target, dipAmount);
    }


    function stake(NftId stakeId, uint256 dipAmount)
        public
        virtual override
    {
        _stake(msg.sender, stakeId, dipAmount);
    }


    function restake(NftId stakeId, NftId newTarget)
        external
        virtual override
        onlyStakeOwner(stakeId)        
    {
        // only owner may restake
        address owner = msg.sender;

        // ensure unstaking is possible
        require(isUnstakingAvailable(stakeId), "ERROR:STK-150:UNSTAKING_NOT_SUPPORTED");

        // staking needs to be possible (might change over time)
        require(isStakingSupported(newTarget), "ERROR:STK-151:STAKING_NOT_SUPPORTED");

        // update rewards of old stake
        StakeInfo storage oldInfo = _info[stakeId];
        _updateRewards(oldInfo);

        // remove stake balance from old target
        _targetStakeBalance[oldInfo.target] -= oldInfo.stakeBalance;

        // calculate new staking amount
        uint256 newStakingAmount = oldInfo.stakeBalance + oldInfo.rewardBalance;

        // update stake, reward balance and reward reserves
        require(_rewardReserves >= oldInfo.rewardBalance, "ERROR:STK-152:REWRD_RESERVES_INSUFFICIENT");
        _rewardReserves -= oldInfo.rewardBalance;
        _rewardBalance -= oldInfo.rewardBalance;
        _stakeBalance += oldInfo.rewardBalance;
 
        // adapt old info
        oldInfo.stakeBalance = 0;
        oldInfo.rewardBalance = 0;
        oldInfo.updatedAt = blockTimestamp();

        // add/create new info
        stakeId = _registry.registerStake(newTarget, owner);
        StakeInfo storage newInfo = _info[stakeId];
        newInfo.id = stakeId;
        newInfo.target = newTarget;
        newInfo.stakeBalance = newStakingAmount;
        newInfo.rewardBalance = 0;
        newInfo.createdAt = blockTimestamp();
        newInfo.lockedUntil = calculateLockingUntil(newTarget);
        newInfo.version = version();

        // add staking amount to new target
        _targetStakeBalance[newInfo.target] += newStakingAmount;

        // restaking leg entry
        emit LogStakingRestaked(oldInfo.target, newInfo.target, owner, stakeId, newStakingAmount);
    }

    function getMessageHelperAddress()
        external
        virtual override
        view
        returns(address messageHelperAddress)
    {
        return address(_messageHelper);
    }


    function isUnstakingAvailable(NftId stakeId)
        public
        virtual
        view 
        returns(bool isAvailable)
    {
        StakeInfo memory info = _info[stakeId];
        if(info.lockedUntil > zeroTimestamp() && blockTimestamp() >= info.lockedUntil) {
            return true;
        }

        return isUnstakingSupported(info.target);
    }


    function getTargetRewardRate(NftId target)
        public
        virtual
        view
        override
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


    function calculateRewardsIncrement(StakeInfo memory info)
        public 
        virtual override
        view
        returns(uint256 rewardsAmount)
    {
        /* solhint-disable not-rely-on-time */
        require(block.timestamp >= toInt(info.updatedAt), "ERROR:STK-200:UPDATED_AT_IN_THE_FUTURE");
        uint256 timeSinceLastUpdate = block.timestamp - toInt(info.updatedAt);
        /* solhint-enable not-rely-on-time */

        // TODO potentially reduce time depending on the time when the bundle has been closed

        UFixed rewardRate = getTargetRewardRate(info.target);
        rewardsAmount = calculateRewards(info.stakeBalance, timeSinceLastUpdate, rewardRate);
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


    function _createStake(
        address owner,
        NftId target, 
        uint256 dipAmount
    )
        internal
        virtual
        returns(NftId stakeId)
    {
        // no validation here, validation is done via calling stake() at the end
        stakeId = _registry.registerStake(target, owner);

        StakeInfo storage info = _info[stakeId];
        info.id = stakeId;
        info.target = target;
        info.stakeBalance = 0;
        info.rewardBalance = 0;
        info.createdAt = blockTimestamp();
        info.lockedUntil = calculateLockingUntil(target);
        info.version = version();

        _stake(owner, stakeId, dipAmount);

        emit LogStakingNewStakeCreated(target, owner, stakeId);
    }


    function _stake(address owner, NftId stakeId, uint256 dipAmount)
        internal
        virtual
    {
        // input validation (stake needs to exist)
        StakeInfo storage info = _info[stakeId];
        require(info.createdAt > zeroTimestamp(), "ERROR:STK-150:STAKE_NOT_EXISTING");
        require(dipAmount > 0, "ERROR:STK-151:STAKING_AMOUNT_ZERO");

        // staking needs to be possible (might change over time)
        require(isStakingSupported(info.target), "ERROR:STK-152:STAKING_NOT_SUPPORTED");

        // update stake info
        _updateRewards(info);
        _increaseStakes(info, dipAmount);
        _collectDip(owner, dipAmount);

        emit LogStakingStaked(info.target, owner, stakeId, dipAmount, info.stakeBalance);
    }


    function _unstake(
        NftId id,
        address user, 
        uint256 amount

    ) 
        internal
        virtual override
    {
        StakeInfo storage info = _info[id];
        require(_canUnstake(info), "ERROR:STK-250:UNSTAKE_NOT_SUPPORTED");
        require(amount > 0, "ERROR:STK-251:UNSTAKE_AMOUNT_ZERO");

        _updateRewards(info);

        bool unstakeAll = (amount == type(uint256).max);
        if(unstakeAll) {
            amount = info.stakeBalance;
        }

        _decreaseStakes(info, amount);
        _withdrawDip(user, amount);

        emit LogStakingUnstaked(
            info.target,
            user,
            info.id,
            amount,
            info.stakeBalance
        );

        if(unstakeAll) {
            _claimRewards(user, info);
        }
    }


    function _canUnstake(StakeInfo storage info)
        internal
        virtual
        view
        returns(bool canUnstake)
    {
        if(info.lockedUntil > zeroTimestamp() && blockTimestamp() >= info.lockedUntil) {
            return true;
        }

        return this.isUnstakingSupported(info.target);
    }

}
