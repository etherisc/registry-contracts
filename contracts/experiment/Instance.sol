// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

// import {AccessControlEnumerableUpgradeable} from "@openzeppelin-upgradeable/contracts/access/AccessControlEnumerableUpgradeable.sol";

import {IChainNft, NftId, toNftId} from "../registry/IChainNft.sol";
import {ChainRegistry} from "./ChainRegistry.sol";

import {IInstance, IComponent, IComponentOwnerService} from "./IServices.sol";


contract Instance is 
    IInstance
    // AccessControlEnumerableUpgradeable
{

    event LogDebug(uint id);

    ChainRegistry private _registry;
    IComponentOwnerService private _componentOwnerService;

    address private _deployer;
    NftId private _nftId;

    mapping(NftId => IComponent.ComponentInfo) private _component;
    mapping(address => IComponent.ComponentInfo) private _componentByAddress;


    constructor(
        address registryAddress,
        address componentOwnerServiceAddress
    )
    {
        _registry = ChainRegistry(registryAddress);
        _componentOwnerService = IComponentOwnerService(componentOwnerServiceAddress);
        _deployer = msg.sender;
    }


    function register(string memory instanceName)
        external
    {
        require(_nftId == toNftId(0), "ERROR_ALREADY_REGISTERED");
        require(msg.sender == _deployer, "ERROR_NOT_DEPLOYER");

        _nftId = _registry.selfRegisterInstance(
            _deployer, // initial instance owner
            address(this),
            instanceName,
            "" // uri
        );
    }


    function registerComponent(
        IComponent.ComponentInfo memory info,
        address deployer
    )
        external
        override
        returns(NftId id)
    {
        // TODO add access control (only component owner service)
        // TODO add validations (prevent duplicate registrations, etc ..)

        id = _registry.selfRegisterComponent(
            deployer, // initial owner
            info.componentAddress,
            _nftId
        );

        _component[id] = info;
        _componentByAddress[info.componentAddress] = info;
    }


    function getComponentInfo(NftId id)
        external
        override
        view 
        returns(IComponent.ComponentInfo memory info)
    {
        return _component[id];
    }


    function setComponentInfo(IComponent.ComponentInfo memory info)
        external
        override
    {
        // write access, limiting access to modules that need access
        require(msg.sender == address(_componentOwnerService), "ERROR:NOT_COMPONENT");
        require(_component[info.id].id == info.id, "ERROR:ID_NOT_EXISTING");

        // so far, only state may be updated
        // component id, address and type are immutable
        _component[info.id].state = info.state;
        _component[info.id].name = info.name;
    }



    function getComponentOwnerService() external override view returns(IComponentOwnerService service) {
        return _componentOwnerService;
    }


    function owner(NftId id) external override view returns(address nftOwner) {
        return _registry.owner(id);
    }


    function instanceId() external view returns(bytes32) {
        return keccak256(
            abi.encodePacked(
                _registry.chainId(), 
                address(this)));
    }

    function nftId() external view returns(NftId id) {
        return _nftId;
    }

    function owner() external view returns(address) {
        return _registry.owner(_nftId);
    }
}
