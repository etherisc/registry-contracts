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
    // keep track of staking rates
    mapping(ChainId chain => mapping(address token => UFixed rate)) internal _stakingRate;

    // link to chain registry
    ChainRegistryV01 internal _registryV01;

    // staking internal data
    Version internal _version;
    Amount internal _rewardReserves;
    UFixed internal _rewardRate;

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
        _rewardReserves = toAmount(0);
        _rewardRate = itof(0);

        transferOwnership(newOwner);
    }

    function setRegistry(ChainRegistryV01 registry)
        external
        virtual
        onlyOwner
    {
        require(registry.version() > zeroVersion(), "ERROR:STK-050:REGISTRY_VERION_ZERO");
        require(
            address(_registryV01) == address(0)
                || registry.version() >= _registryV01.version(),
            "ERROR:STK-051:REGISTRY_VERION_DECREASING");

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

    function setRewardRate(UFixed rate)
        external
        virtual override
        onlyOwner
    {

    }

    function increaseRewardReserves(Amount dips)
        external
        virtual override
        onlyOwner
    {

    }

    //--- view and pure functions ------------------//

    function stakingRate(ChainId chain, address token)
        external 
        virtual override
        returns(UFixed rate)
    {

    }

    function rewardRate()
        external
        virtual override
        returns(UFixed rate)
    {

    }

    function rewardReserves()
        external
        virtual override
        returns(Amount dips)
    {

    }


    function getRegistry() external virtual view returns(ChainRegistryV01) {
        return _registryV01;
    }

}
