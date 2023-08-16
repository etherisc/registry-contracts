// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {IOwnable} from "../../registry/IRegistry.sol";

interface IAccess {

    struct RoleInfo {
        bytes32 id;
        string name;
        bool isActive;
    }
}


interface IAccessOwnerService is IAccess {

    function createRole(IAccessModule module, string memory roleName) 
        external
        returns(bytes32 role);

    function disableRole(IAccessModule module, bytes32 role) 
        external;        

    function enableRole(IAccessModule module, bytes32 role) 
        external;       

    function grantRole(IAccessModule module, bytes32 role, address member) 
        external;       

    // function revokeRole(IAccessModule module, bytes32 role, address member) 
    //     external;       
}


interface IAccessModule is 
    IOwnable,
    IAccess
{

    function setRoleInfo(RoleInfo memory info)
        external
        returns(bytes32 roleId);

    function getRoleInfo(bytes32 role)
        external
        view
        returns(RoleInfo memory info);

    function getRole(uint256 idx)
        external
        view
        returns(bytes32 role);

    function getRoleCount()
        external
        view
        returns(uint256 roles);

    function getRoleMemberCount(bytes32 role)
        external
        view
        returns(uint256 roleMembers);

    function getRoleMember(bytes32 role, uint256 idx)
        external
        view
        returns(address roleMembers);

    function grantRole(bytes32 role, address member)
        external;       

    function revokeRole(bytes32 role, address member)
        external;       

    function getAccessOwnerService()
        external
        view
        returns(IAccessOwnerService);
}