// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "../shared/BaseTypes.sol";
import "../shared/UFixedMath.sol";
import "../shared/VersionedOwnable.sol";

import "../registry/ChainRegistryV01.sol";

import "./IStaking.sol";

// registers dip relevant objects for this chain
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

    // staking wallet (ccount holding dips)
    uint256 private _stakeBalance;
    address private _stakingWallet;

    // keep track of staking rates
    mapping(ChainId chain => mapping(address token => UFixed rate)) internal _stakingRate;

    // link to chain registry
    ChainRegistryV01 internal _registryV01;

    // staking internal data
    Version internal _version;

    IERC20Metadata internal _dip; 
    uint256 internal _rewardReserves;
    UFixed internal _rewardRate;
    UFixed internal _rewardRateMax;

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
    }


    function setStakingRate(ChainId chain, address token, UFixed rate)
        external
        virtual override
        onlyOwner
    {
        // TODO refactor from old impl
        // require(_registry.isRegisteredToken(token, chainId), "ERROR:STK-020:TOKEN_NOT_REGISTERED");
        // require(newStakingRate > 0, "ERROR:STK-021:STAKING_RATE_ZERO");

        // uint256 oldStakingRate = _stakingRate[token][chainId];
        // _stakingRate[token][chainId] = newStakingRate;
    }


    function setRewardRate(UFixed newRewardRate)
        external
        virtual override
        onlyOwner
    {
        require(newRewardRate <= _rewardRateMax, "ERROR:STK-070:REWARD_EXCEEDS_MAX_VALUE");
        UFixed oldRewardRate = _rewardRate;

        _rewardRate = newRewardRate;
    }


    function refillRewardReserves(uint256 dipAmount)
        external
        virtual override
    {
        require(dipAmount > 0, "ERROR:STK-080:DIP_AMOUNT_ZERO");

        address user = msg.sender;
        _collectDip(user, dipAmount);
    }


    function withdrawRewardReserves(uint256 dipAmount)
        external
        virtual override
        onlyOwner
    {
        require(dipAmount > 0, "ERROR:STK-090:DIP_AMOUNT_ZERO");
        require(_rewardReserves >= dipAmount, "ERROR:STK-091:DIP_RESERVES_INSUFFICIENT");

        _rewardReserves -= dipAmount;

        _withdrawDip(dipAmount);
    }

    //--- view and pure functions ------------------//

    function stakingRate(ChainId chain, address token)
        external 
        virtual override
        returns(UFixed rate)
    {

    }


    function maxRewardRate()
        external
        view
        returns(UFixed)
    {
        return _rewardRateMax;
    }


    function rewardRate()
        external
        virtual override
        view
        returns(UFixed)
    {
        return _rewardRate;
    }


    function rewardReserves()
        external
        virtual override
        view
        returns(uint256 dips)
    {
        return _rewardReserves;
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


    function getDip() 
        external 
        virtual
        view 
        returns(IERC20Metadata)
    {
        return _dip;
    }


    function getRegistry()
        external 
        virtual 
        view 
        returns(ChainRegistryV01)
    {
        return _registryV01;
    }

    //--- internal functions ------------------//

    function _collectDip(address user, uint256 amount)
        internal
        virtual
    {
        _rewardReserves += amount;
        _dip.transferFrom(user, _stakingWallet, amount);
    }


    function _withdrawDip(uint256 amount)
        internal
        virtual
    {
        if(_stakingWallet != address(this)) {
            _dip.transferFrom(_stakingWallet, owner(), amount);
        } else {
            _dip.transfer(owner(), amount);
        }
    }
}
