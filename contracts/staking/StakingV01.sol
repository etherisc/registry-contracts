// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";

import "../shared/BaseTypes.sol";
import "../shared/UFixedMath.sol";
import "../shared/VersionedOwnable.sol";

import "../registry/IInstanceServiceFacade.sol";
import "../registry/ChainRegistryV01.sol";

import "./IStaking.sol";


contract StakingV01 is
    BaseTypes,
    UFixedType,
    VersionedOwnable,
    IStaking
{
    uint256 public constant MAINNET_ID = 1;
    // dip coordinates
    address public constant DIP_CONTRACT_ADDRESS = 0xc719d010B63E5bbF2C0551872CD5316ED26AcD83;
    uint256 public constant DIP_DECIMALS = 18;

    // max annual dip staking reward rate at 33.3%
    uint256 public constant MAX_REWARD_RATE_VALUE = 333;
    int8 public constant MAX_REWARD_RATE_EXP = -3;
    uint256 public constant YEAR_DURATION = 365 days;

    uint256 public constant BUNDLE_LIFETIME_DEFAULT = 6 * 30 * 24 * 3600;

    // staking wallet (ccount holding dips)
    IERC20Metadata internal _dip; 

    UFixed internal _rewardRate; // current apr for staking rewards
    UFixed internal _rewardRateMax; // max apr for staking rewards
    uint256 internal _rewardBalance; // current balance of accumulated rewards 
    uint256 internal _rewardReserves; // available funds to fund reward payments

    uint256 private _stakeBalance; // current balance of staked dips
    address private _stakingWallet; // address that holds staked dips and reward reserves

    // keep track of object types supported for staking
    mapping(ObjectType targetType => bool isSupported) internal _stakingSupported;

    // keep track of stakes
    mapping(NftId id => StakeInfo info) internal _info; // metadata per stake
    mapping(NftId target => uint256 amountStaked) internal _targetStakeBalance; // current sum of stakes per target

    // keep track of staking rates
    mapping(ChainId chain => mapping(address token => UFixed rate)) internal _stakingRate;

    // link to chain registry
    ChainRegistryV01 internal _registryV01;

    // staking internal data
    Version internal _version;


    modifier onlySameChain(NftId id) {
        require(_registryV01.getNftInfo(id).chain == thisChainId(),
        "ERROR:STK-001:DIFFERENT_CHAIN_NOT_SUPPORTET");
        _;
    }


    modifier onlyApprovedToken(ChainId chain, address token) {
        NftId id = _registryV01.getNftId(chain, token);
        require(gtz(id), "ERROR:STK-005:NOT_REGISTERED");
        IChainRegistry.NftInfo memory info = _registryV01.getNftInfo(id);
        require(info.t == _registryV01.TOKEN(), "ERROR:STK-006:NOT_TOKEN");
        require(
            info.state == IChainRegistry.ObjectState.Approved, 
            "ERROR:STK-007:TOKEN_NOT_APPROVED");
        _;
    }


    modifier onlyStakeOwner(NftId id) {
        require(isStakeOwner(id, msg.sender), "ERROR:STK-010:USER_NOT_OWNER");
        _;
    }


    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(
            toVersionPart(0),
            toVersionPart(0),
            toVersionPart(1));
    }

    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activateAndSetOwner(address implementation, address newOwner)
        external
        virtual override
        initializer
    {
        // ensure proper version history
        _activate(implementation);

        // initialize open zeppelin contracts
        __Ownable_init();

        // set main internal variables
        _version = version();

        _dip = IERC20Metadata(DIP_CONTRACT_ADDRESS);

        _stakeBalance = 0;
        _stakingWallet = address(this);

        _rewardReserves = 0;
        _rewardRate = itof(0);
        _rewardRateMax = itof(MAX_REWARD_RATE_VALUE, MAX_REWARD_RATE_EXP);

        transferOwnership(newOwner);
    }


    // only for testing purposes!
    // decide if this should be restricted to ganache chain ids
    function setDipContract(address dipToken) 
        external
        virtual
        onlyOwner
    {
        require(block.chainid != MAINNET_ID, "ERROR:STK-040:DIP_ADDRESS_CHANGE_NOT_ALLOWED_ON_MAINNET");
        require(dipToken != address(0), "ERROR:STK-041:DIP_CONTRACT_ADDRESS_ZERO");

        _dip = IERC20Metadata(dipToken);
        require(_dip.decimals() == DIP_DECIMALS, "ERROR:STK-042:DIP_DECIMALS_INVALID");
    }

    // sets the on-chain registry that keeps track of all protocol objects on this chain
    function setRegistry(ChainRegistryV01 registry)
        external
        virtual
        onlyOwner
    {
        require(registry.version() > zeroVersion(), "ERROR:STK-050:REGISTRY_VERSION_ZERO");
        require(
            address(_registryV01) == address(0)
                || registry.version() >= _registryV01.version(),
            "ERROR:STK-051:REGISTRY_VERSION_DECREASING");

        _registryV01 = registry;

        // explicit setting of staking support per object type
        _stakingSupported[_registryV01.PROTOCOL()] = false;
        _stakingSupported[_registryV01.INSTANCE()] = false;
        _stakingSupported[_registryV01.PRODUCT()] = false;
        _stakingSupported[_registryV01.ORACLE()] = false;
        _stakingSupported[_registryV01.RISKPOOL()] = false;
        _stakingSupported[_registryV01.BUNDLE()] = true;
    }


    function refillRewardReserves(uint256 dipAmount)
        external
        virtual override
    {
        require(dipAmount > 0, "ERROR:STK-080:DIP_AMOUNT_ZERO");

        address user = msg.sender;
        _collectRewardDip(user, dipAmount);
    }


    function withdrawRewardReserves(uint256 dipAmount)
        external
        virtual override
        onlyOwner
    {
        require(dipAmount > 0, "ERROR:STK-090:DIP_AMOUNT_ZERO");

        _withdrawRewardDip(owner(), dipAmount);
    }


    function setRewardRate(UFixed newRewardRate)
        external
        virtual override
        onlyOwner
    {
        require(newRewardRate <= _rewardRateMax, "ERROR:STK-100:REWARD_EXCEEDS_MAX_VALUE");
        UFixed oldRewardRate = _rewardRate;

        _rewardRate = newRewardRate;

        emit LogStakingRewardRateSet(owner(), oldRewardRate, _rewardRate);
    }


    function setStakingRate(
        ChainId chain,
        address token,
        UFixed newStakingRate
    )
        external
        virtual override
        onlyOwner
        onlyApprovedToken(chain, token)
    {
        require(gtz(newStakingRate), "ERROR:STK-110:STAKING_RATE_ZERO");

        UFixed oldStakingRate = _stakingRate[chain][token];
        _stakingRate[chain][token] = newStakingRate;

        emit LogStakingStakingRateSet(owner(), chain, token, oldStakingRate, newStakingRate);
    }


    function createStake(NftId target, uint256 dipAmount)
        external
        virtual override
        returns(NftId stakeId)
    {
        // no validation here, validation is done via calling stake() at the end
        address user = msg.sender;
        stakeId = _registryV01.registerStake(target, user);

        StakeInfo storage info = _info[stakeId];
        info = _info[stakeId];
        info.id = stakeId;
        info.target = target;
        info.stakeBalance = 0;
        info.rewardBalance = 0;
        info.createdAt = blockTimestamp();
        info.version = version();

        emit LogStakingNewStake(target, user, stakeId);

        stake(stakeId, dipAmount);
    }


    function stake(NftId stakeId, uint256 dipAmount)
        public
        virtual override
    {
        // input validation (stake needs to exist)
        StakeInfo storage info = _info[stakeId];
        require(info.createdAt > zeroTimestamp(), "ERROR:STK-150:STAKE_NOT_EXISTING");
        require(dipAmount > 0, "ERROR:STK-151:STAKING_AMOUNT_ZERO");

        // staking needs to be possible (might change over time)
        require(isStakingSupported(info.target), "ERROR:STK-152:STAKING_NOT_SUPPORTED");
        address user = msg.sender;

        // update stake info
        _updateRewards(info);
        _increaseStakes(info, dipAmount);
        _collectDip(user, dipAmount);

        emit LogStakingStaked(info.target, user, stakeId, dipAmount, info.stakeBalance);
    }


    function unstake(NftId stakeId, uint256 amount)
        external
        virtual override
        onlyStakeOwner(stakeId)        
    {
        _unstake(stakeId, msg.sender, amount);
    }


    function unstakeAndClaimRewards(NftId stakeId)
        external
        virtual override
        onlyStakeOwner(stakeId)     
    {
        _unstake(stakeId, msg.sender, type(uint256).max);
    }


    function claimRewards(NftId stakeId)
        external
        virtual override
        onlyStakeOwner(stakeId)        
    {
        address user = msg.sender;
        StakeInfo storage info = _info[stakeId];

        _claimRewards(user, info);
    }

    //--- view and pure functions ------------------//


    function rewardRate()
        external
        virtual override
        view
        returns(UFixed)
    {
        return _rewardRate;
    }


    function rewardBalance()
        external
        virtual override
        view
        returns(uint256 dips)
    {
        return _rewardBalance;
    }


    function rewardReserves()
        external
        virtual override
        view
        returns(uint256 dips)
    {
        return _rewardReserves;
    }


    function stakingRate(ChainId chain, address token)
        external 
        virtual override
        view
        returns(UFixed rate)
    {
        return _stakingRate[chain][token];
    }


    function getStakingWallet() 
        external
        virtual override
        view
        returns(address stakingWallet)
    {
        return _stakingWallet;
    }


    function getDip() 
        external 
        virtual override
        view 
        returns(IERC20Metadata dip)
    {
        return _dip;
    }


    function isStakeOwner(NftId stakeId, address user)
        public
        virtual override
        view
        returns(bool isOwner)
    {
        return _registryV01.ownerOf(NftId.unwrap(stakeId)) == user;
    }


    function getInfo(NftId id)
        external override
        view
        returns(StakeInfo memory info)
    {
        require(_info[id].createdAt > zeroTimestamp(), "ERROR:STK-200:STAKE_INFO_NOT_EXISTING");
        return _info[id];
    }


    function isStakingSupportedForType(ObjectType targetType)
        external
        virtual override
        view
        returns(bool isSupported)
    {
        return _stakingSupported[targetType];
    }


    function isStakingSupported(NftId target)
        public
        virtual override
        view 
        returns(bool isSupported)
    {
        ObjectType targetType = _registryV01.getNftInfo(target).t;
        if(!_stakingSupported[targetType]) {
            return false;
        }

        // deal with special cases
        if(targetType == _registryV01.BUNDLE()) {
            return _isStakingSupportedForBundle(target);
        }

        return true;
    }


    function isUnstakingSupported(NftId target)
        public
        virtual override
        view 
        returns(bool isSupported)
    {
        ObjectType targetType = _registryV01.getNftInfo(target).t;
        if(!_stakingSupported[targetType]) {
            return false;
        }

        // deal with special cases
        if(targetType == _registryV01.BUNDLE()) {
            return _isUnstakingSupportedForBundle(target);
        }

        return true;
    }


    function calculateRewardsIncrement(StakeInfo memory stakeInfo)
        public 
        virtual override
        view
        returns(uint256 rewardsAmount)
    {
        uint256 timeSinceLastUpdate = block.timestamp - toInt(stakeInfo.updatedAt);

        // TODO potentially reduce time depending on the time when the bundle has been closed

        rewardsAmount = calculateRewards(stakeInfo.stakeBalance, timeSinceLastUpdate);
    }


    function calculateRewards(
        uint256 amount,
        uint256 duration
    ) 
        public 
        virtual override
        view
        returns(uint256 rewardAmount) 
    {
        UFixed yearFraction = itof(duration) / itof(YEAR_DURATION);
        UFixed rewardDuration = _rewardRate * yearFraction;
        rewardAmount = ftoi(itof(amount) * rewardDuration);
    }


    function calculateRequiredStaking(
        ChainId chain,
        address token,
        uint256 tokenAmount
    )
        external
        virtual override
        view 
        returns(uint256 dipAmount)
    {
        require(gtz(_stakingRate[chain][token]), "ERROR:STK-210:TOKEN_STAKING_RATE_NOT_SET");

        UFixed rate = _stakingRate[chain][token];
        int8 decimals = int8(IERC20Metadata(token).decimals());
        UFixed dip = itof(tokenAmount, int8(uint8(DIP_DECIMALS)) - decimals) / rate;

        return ftoi(dip);
    }


    function calculateCapitalSupport(
        ChainId chain,
        address token,
        uint256 dipAmount
    )
        public
        virtual override
        view
        returns(uint256 tokenAmount)
    {
        require(gtz(_stakingRate[chain][token]), "ERROR:STK-211:TOKEN_STAKING_RATE_NOT_SET");

        UFixed rate = _stakingRate[chain][token];
        int8 decimals = int8(IERC20Metadata(token).decimals());
        UFixed support = itof(dipAmount, decimals - int8(uint8(DIP_DECIMALS))) * _stakingRate[chain][token];

        return ftoi(support);
    }


    function capitalSupport(NftId target)
        external
        virtual override
        view 
        returns(uint256 capitalAmount)
    {
        IChainRegistry.NftInfo memory info = _registryV01.getNftInfo(target);

        // check target type staking support
        require(_stakingSupported[info.t], "ERROR:STK-220:TARGET_TYPE_NOT_SUPPORTED");
        require(info.t == _registryV01.BUNDLE(), "ERROR:STK-221:TARGET_TYPE_NOT_BUNDLE");

        (,,, address token, ) = _registryV01.decodeBundleData(target);

        return calculateCapitalSupport(
            info.chain, 
            token, 
            _targetStakeBalance[target]);
    }


    function toRate(uint256 value, int8 exp)
        external
        virtual override
        pure
        returns(UFixed)
    {
        return itof(value, exp);
    }


    function rateDecimals()
        external
        virtual override
        pure
        returns(uint256)
    {
        return decimals();
    }


    function getRegistry()
        external 
        virtual 
        view 
        returns(ChainRegistryV01)
    {
        return _registryV01;
    }


    function maxRewardRate()
        external
        view
        returns(UFixed)
    {
        return _rewardRateMax;
    }


    function getBundleState(NftId target)
        public
        view
        onlySameChain(target)
        returns(
            IChainRegistry.ObjectState objectState,
            IInstanceServiceFacade.BundleState bundleState,
            Timestamp expiryAt
        )
    {
        IChainRegistry.NftInfo memory info = _registryV01.getNftInfo(target);
        require(info.t == _registryV01.BUNDLE(), "ERROR:STK-230:OBJECT_TYPE_NOT_BUNDLE");

        // fill in object stae from registry info
        objectState = info.state;

        // read bundle data directly from instance/riskpool
        // can be done thanks to onlySameChain modifier
        (
            bytes32 instanceId,
            ,
            uint256 bundleId
            ,
            ,
        ) = _registryV01.decodeBundleData(target);

        IInstanceServiceFacade instanceService = _registryV01.getInstanceServiceFacade(instanceId);
        IInstanceServiceFacade.Bundle memory bundle = instanceService.getBundle(bundleId);
        
        // fill in other properties from bundle info
        bundleState = bundle.state;
        // approx to actual expiry at, good enough for initial staking
        // TODO once expiry at is available via instance service replace
        // this by actual value
        expiryAt = toTimestamp(bundle.createdAt + BUNDLE_LIFETIME_DEFAULT);
    }


    //--- internal functions ------------------//


    function _isStakingSupportedForBundle(NftId target)
        internal
        virtual
        view
        returns(bool isSupported)
    {
        (
            IChainRegistry.ObjectState objectState,
            IInstanceServiceFacade.BundleState bundleState,
            Timestamp expiryAt
        ) = getBundleState(target);

        // only active bundles are available for staking
        if(bundleState != IInstanceServiceFacade.BundleState.Active) {
            return false;
        }

        // only non-expired bundles are available for staking
        if(expiryAt > zeroTimestamp() && expiryAt < blockTimestamp()) {
            return false;
        }

        return true;
    }


    function _isUnstakingSupportedForBundle(NftId target)
        internal
        virtual
        view
        returns(bool isSupported)
    {
        (
            IChainRegistry.ObjectState objectState,
            IInstanceServiceFacade.BundleState bundleState,
            Timestamp expiryAt
        ) = getBundleState(target);

        // only closed or burned bundles are available for staking
        if(bundleState == IInstanceServiceFacade.BundleState.Closed
            || bundleState == IInstanceServiceFacade.BundleState.Burned)
        {
            return true;
        }

        // expired bundles are available for unstaking
        if(expiryAt > zeroTimestamp() && expiryAt < blockTimestamp()) {
            return true;
        }

        return false;
    }


    function _increaseStakes(
        StakeInfo storage info,
        uint256 amount
    )
        internal
        virtual
    {
        _targetStakeBalance[info.target] += amount;
        _stakeBalance += amount;

        info.stakeBalance += amount;
        info.updatedAt = blockTimestamp();
    }


    function _unstake(
        NftId id,
        address user, 
        uint256 amount
    ) 
        internal
        virtual
    {
        StakeInfo storage info = _info[id];
        require(this.isUnstakingSupported(info.target), "ERROR:STK-250:UNSTAKE_NOT_SUPPORTED");
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


    function _claimRewards(
        address user,
        StakeInfo storage info
    )
        internal
        virtual
    {
        uint256 amount = info.rewardBalance;

        // ensure reward payout is within avaliable reward reserves
        if(amount > _rewardReserves) {
            amount = _rewardReserves;
        }

        // book keeping
        _decreaseRewards(info, amount);
        _rewardReserves -= amount;

        // transfer of dip
        _withdrawDip(user, amount);
    }


    function _updateRewards(StakeInfo storage info)
        internal
        virtual
    {
        uint256 amount = calculateRewardsIncrement(info);
        _rewardBalance += amount;

        info.rewardBalance += amount;
        info.updatedAt = blockTimestamp();

        emit LogStakingRewardsUpdated(
            info.id,
            amount,
            info.rewardBalance
        );
    }


    function _decreaseStakes(
        StakeInfo storage info,
        uint256 amount
    )
        internal
        virtual
    {
        require(amount <= info.stakeBalance, "ERROR:STK-270:UNSTAKING_AMOUNT_EXCEEDS_STAKING_BALANCE");

        _targetStakeBalance[info.target] -= amount;
        _stakeBalance -= amount;

        info.stakeBalance -= amount;
        info.updatedAt = blockTimestamp();
    }


    function _decreaseRewards(StakeInfo storage info, uint256 amount)
        internal
        virtual
    {
        info.rewardBalance -= amount;
        info.updatedAt = blockTimestamp();

        _rewardBalance -= amount;

        emit LogStakingRewardsClaimed(
            info.id,
            amount,
            info.rewardBalance
        );
    }


    function _collectRewardDip(address user, uint256 amount)
        internal
        virtual
    {
        _rewardReserves += amount;
        _collectDip(user, amount);

        emit LogStakingRewardReservesIncreased(user, amount, _rewardReserves);
    }


    function _withdrawRewardDip(address user, uint256 amount)
        internal
        virtual
    {
        require(_rewardReserves >= amount, "ERROR:STK-280:DIP_RESERVES_INSUFFICIENT");

        _rewardReserves -= amount;
        _withdrawDip(owner(), amount);

        emit LogStakingRewardReservesDecreased(user, amount, _rewardReserves);
    }


    function _collectDip(address user, uint256 amount)
        internal
        virtual
    {
        _dip.transferFrom(user, _stakingWallet, amount);
    }


    function _withdrawDip(address user, uint256 amount)
        internal
        virtual
    {
        require(_dip.balanceOf(_stakingWallet) >= amount, "ERROR:STK-290:DIP_BALANCE_INSUFFICIENT");

        if(_stakingWallet != address(this)) {
            _dip.transferFrom(_stakingWallet, user, amount);
        } else {
            _dip.transfer(user, amount);
        }
    }
}
