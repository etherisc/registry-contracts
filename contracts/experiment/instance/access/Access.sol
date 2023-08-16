// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

// role admin handling of oz doesn't fit module/controller pattern
// import {AccessControlEnumerable} from "@openzeppelin/contracts/access/AccessControlEnumerable.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

import {IAccessModule, IAccessOwnerService} from "./IAccess.sol";


abstract contract AccessModule is
    IAccessModule
{
    using EnumerableSet for EnumerableSet.AddressSet;

    mapping(bytes32 role => RoleInfo info) private _info;
    bytes32 [] private _roles;

    mapping(bytes32 role => mapping(address member => bool isMember)) private _isRoleMember;
    mapping(bytes32 role => EnumerableSet.AddressSet) private _roleMembers;

    IAccessOwnerService private _ownerService;

    modifier onlyAccessOwnerService() {
        require(address(_ownerService) == msg.sender, "ERROR:ACM-001:NOT_OWNER_SERVICE");
        _;
    }

    constructor(address ownerServiceAddress) {
        _ownerService = IAccessOwnerService(ownerServiceAddress);
    }


    function setRoleInfo(RoleInfo memory info)
        external
        override
        onlyAccessOwnerService
        returns(bytes32 role)
    {
        role = info.id;

        if(role == bytes32(0)) {
            role = keccak256(abi.encode(info.name));
            // TODO check that this is a new role id

            info.id = role;
            _roles.push(role);

            // TODO add logging
        }

        _info[role] = info;

        // TODO add logging
    }


    function getRoleInfo(bytes32 role)
        external
        override
        view
        returns(RoleInfo memory info)
    {
        return _info[role];
    }


    function getRole(uint256 idx)
        external
        override
        view
        returns(bytes32 role)
    {
        return _roles[idx];
    }


    function getRoleCount()
        external
        override
        view
        returns(uint256 roles)
    {
        return _roles.length;
    }        

    function getRoleMemberCount(bytes32 role)
        public
        override
        view
        returns(uint256 roleMembers)
    {
        return _roleMembers[role].length();
    }

    function getRoleMember(bytes32 role, uint256 idx)
        public
        override
        view
        returns(address roleMembers)
    {
        return _roleMembers[role].at(idx);
    }

    function grantRole(bytes32 role, address member) 
        external
        override     
        onlyAccessOwnerService
    {
        require(_info[role].id == role, "ERROR:ACM-010:ROLE_NOT_EXISTING");
        require(_info[role].isActive, "ERROR:ACM-011:ROLE_NOT_ACTIVE");

        _isRoleMember[role][member] = true;
        _roleMembers[role].add(member);

        // TODO add logging
    }

    function revokeRole(bytes32 role, address member) 
        external
        override     
        onlyAccessOwnerService
    {
        require(_info[role].id == role, "ERROR:ACM-020:ROLE_NOT_EXISTING");

        _isRoleMember[role][member] = false;
        _roleMembers[role].remove(member);

        // TODO add logging
    }

    function getAccessOwnerService()
        external
        override
        view
        returns(IAccessOwnerService)
    {
        return _ownerService;
    }
   
}


contract AccessOwnerService is
    IAccessOwnerService
{

    modifier onlyModuleOwner(IAccessModule module) {
        require(
            msg.sender == module.getOwner(),
            "ERROR:AOS-001:NOT_MODULE_OWNER"
        );
        _;
    }

    function createRole(IAccessModule module, string memory roleName) 
        external
        override
        onlyModuleOwner(module)
        returns(bytes32 role)
    {
        RoleInfo memory info = RoleInfo(
            0,
            roleName,
            true
        );

        role = module.setRoleInfo(info);

        // TODO add logging
    }

    function disableRole(IAccessModule module, bytes32 role) 
        external
        override
        onlyModuleOwner(module)
    {
        require(module.getRoleInfo(role).id == role, "ERROR:AOS-001:ROLE_DOES_NOT_EXIST");

        RoleInfo memory info = module.getRoleInfo(role);
        info.isActive = true;
        module.setRoleInfo(info);

        // TODO add logging
    }   

    function enableRole(IAccessModule module, bytes32 role) 
        external
        override       
        onlyModuleOwner(module)
    {
        require(module.getRoleInfo(role).id == role, "ERROR:AOS-002:ROLE_DOES_NOT_EXIST");

        RoleInfo memory info = module.getRoleInfo(role);
        info.isActive = false;
        module.setRoleInfo(info);

        // TODO add logging
    }   

    function grantRole(IAccessModule module, bytes32 role, address member) 
        external
        override
        onlyModuleOwner(module)
    {
        require(module.getRoleInfo(role).id == role, "ERROR:AOS-003:ROLE_DOES_NOT_EXIST");
        require(module.getRoleInfo(role).isActive, "ERROR:AOS-004:ROLE_NOT_ACTIVE");

        module.grantRole(role, member);

        // TODO add logging
    }

}