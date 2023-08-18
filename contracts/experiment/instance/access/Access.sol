// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

// role admin handling of oz doesn't fit nft ownability
// import {AccessControlEnumerable} from "@openzeppelin/contracts/access/AccessControlEnumerable.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

import {IAccessModule} from "./IAccess.sol";


abstract contract AccessModule is
    IAccessModule
{
    string constant public PRODUCT_OWNER = "ProductOwner";
    string constant public ORACLE_OWNER = "OracleOwner";
    string constant public POOL_OWNER = "PoolOwner";

    using EnumerableSet for EnumerableSet.AddressSet;

    mapping(bytes32 role => RoleInfo info) private _info;
    bytes32 [] private _roles;

    bytes32 _productOwnerRole;
    bytes32 _oracleOwnerRole;
    bytes32 _poolOwnerRole;

    mapping(bytes32 role => mapping(address member => bool isMember)) private _isRoleMember;
    mapping(bytes32 role => EnumerableSet.AddressSet) private _roleMembers;

    modifier onlyOwner() {
        require(msg.sender == this.getOwner(), "ERROR:ACM-001:NOT_OWNER");
        _;
    }

    constructor() {
        _productOwnerRole = _createRole(PRODUCT_OWNER);
        _oracleOwnerRole = _createRole(ORACLE_OWNER);
        _poolOwnerRole = _createRole(POOL_OWNER);
    }


    function getComponentTypeRole(uint256 cType)
        external
        view
        override
        returns(bytes32 role)
    {
        if(cType == this.getRegistry().PRODUCT()) {
            return _productOwnerRole;
        }
        if(cType == this.getRegistry().POOL()) {
            return _poolOwnerRole;
        }
        if(cType == this.getRegistry().ORACLE()) {
            return _oracleOwnerRole;
        }
    }


    function createRole(string memory roleName) 
        external
        override
        onlyOwner
        returns(bytes32 role)
    {
        return _createRole(roleName);
    }

    function _createRole(string memory roleName) 
        internal
        returns(bytes32 role)
    {
        RoleInfo memory info = RoleInfo(
            0,
            roleName,
            true
        );

        role = _setRoleInfo(info);

        
    }

    // TODO move to module
    function disableRole(bytes32 role) 
        external
        override
        onlyOwner
    {
        RoleInfo memory info = _info[role];
        require(info.id == role, "ERROR:AOS-001:ROLE_DOES_NOT_EXIST");

        info.isActive = false;
        _setRoleInfo(info);

        
    }   

    // TODO move to module
    function enableRole(bytes32 role) 
        external
        override       
        onlyOwner
    {
        RoleInfo memory info = _info[role];
        require(info.id == role, "ERROR:AOS-002:ROLE_DOES_NOT_EXIST");

        info.isActive = true;
        _setRoleInfo(info);

        
    }   

    function grantRole(bytes32 role, address member) 
        external
        override     
        onlyOwner
    {
        require(_info[role].id == role, "ERROR:ACM-010:ROLE_NOT_EXISTING");
        require(_info[role].isActive, "ERROR:ACM-011:ROLE_NOT_ACTIVE");

        _isRoleMember[role][member] = true;
        _roleMembers[role].add(member);

        
    }


    function revokeRole(bytes32 role, address member) 
        external
        override     
        onlyOwner
    {
        require(_info[role].id == role, "ERROR:ACM-020:ROLE_NOT_EXISTING");

        _isRoleMember[role][member] = false;
        _roleMembers[role].remove(member);

        
    }


    function hasRole(bytes32 role, address member)
        external
        view
        override
        returns(bool)
    {
        return _isRoleMember[role][member];
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

    function getRoleForName(string memory roleName)
        public
        override
        pure
        returns(bytes32 role)
    {
        return keccak256(abi.encode(roleName));
    }


    function _setRoleInfo(RoleInfo memory info)
        internal
        returns(bytes32 role)
    {
        role = info.id;

        if(role == bytes32(0)) {
            role = getRoleForName(info.name);
            // TODO check that this is a new role id

            info.id = role;
            _roles.push(role);

            
        }

        _info[role] = info;

        
    }
}
