// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {IChainNft, NftId, toNftId} from "../registry/IChainNft.sol";

// import {ComponentOwnerService} from "./ComponentOwnerService.sol";

interface IComponent {

    enum ComponentType {
        Undefined,
        Oracle,
        Product,
        Riskpool
    }


    enum ComponentState {
        Undefined,
        Created,
        Proposed,
        Declined,
        Active,
        Paused,
        Suspended,
        Archived
    }


    struct ComponentInfo {
        NftId id;
        address componentAddress;
        ComponentType componentType;
        ComponentState state;
        string name;
    }


    function componentType() external pure returns(ComponentType);
    function deployer() external view returns(address);

    function nftId() external view returns(NftId id);
    function owner() external view returns(address);
    function name() external view returns(string memory);
}


interface IInstance {

    function getComponentOwnerService() external view returns(IComponentOwnerService service);

    function registerComponent(IComponent.ComponentInfo memory info, address deployer) external returns(NftId id);
    function getComponentInfo(NftId id) external view returns(IComponent.ComponentInfo memory info);
    function setComponentInfo(IComponent.ComponentInfo memory info) external;

    function owner(NftId id) external view returns(address owner);
}


interface IComponentOwnerService {
    function register(IInstance instance, IComponent component) external returns(NftId id);
    function pause(IInstance instance, NftId id) external;
    function resume(IInstance instance, NftId id) external;
}


interface IInstanceOwnerService {
    function createRole(bytes32 role) external;
    function grantRole(bytes32 role, address principal) external;
}


interface IInstanceService {
    function hasRole(address principal, bytes32 role) external;

    function isRegistered(IComponent component) external;
}


