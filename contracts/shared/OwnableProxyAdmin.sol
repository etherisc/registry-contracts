// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {TransparentUpgradeableProxy} from "@openzeppelin/contracts/proxy/transparent/TransparentUpgradeableProxy.sol";

import {VersionedOwnable} from "./VersionedOwnable.sol";

contract OwnableProxyAdmin is
    Ownable
{
    string public constant ACTIVATE_SIGNATURE = "activate(address,address)";
    string public constant ACTIVATE_AND_SET_OWNER_SIGNATURE = "activateAndSetOwner(address,address,address)";

    VersionedOwnable private _implementation;
    TransparentUpgradeableProxy private _proxy;

    constructor(
        VersionedOwnable implementation
    )
        Ownable()
    {
        require(address(implementation) != address(0), "ERROR:PXA-001:IMPLEMENTATION_ZERO");
        _implementation = implementation;
    }


    function setProxy(TransparentUpgradeableProxy proxy)
        external
        onlyOwner
    {
        require(address(_proxy) == address(0), "ERROR:PXA-010:PROXY_SET_ALREADY");
        require(address(proxy) != address(0), "ERROR:PXA-011:PROXY_ZERO");
        _proxy = proxy;
    }


    function getProxyCallData(
        address implementation,
        address implementationOwner,
        address activatedBy
    )
        external
        pure
        returns(bytes memory data)
    {
        return abi.encodeWithSignature(
            ACTIVATE_AND_SET_OWNER_SIGNATURE,
            implementation,
            implementationOwner,
            activatedBy);
    }


    function upgrade(VersionedOwnable newImplementation) 
        external
        onlyOwner
    {
        require(address(_proxy) != address(0), "ERROR:PXA-020:PROXY_NOT_SET");
        require(address(newImplementation) != address(0), "ERROR:PXA-021:IMPLEMENTATION_ZERO");
        require(address(newImplementation) != address(_implementation), "ERROR:PXA-022:IMPLEMENTATION_NOT_NEW");

        address activatedBy = msg.sender;
    
        _implementation = newImplementation;
        _proxy.upgradeToAndCall(
            address(newImplementation), 
            abi.encodeWithSignature(
                ACTIVATE_SIGNATURE,
                address(newImplementation),
                activatedBy)
        );
    }


    function transferAdmin(address newAdmin)
        external
        onlyOwner
    {
        require(newAdmin != address(0), "ERROR:PXA-030:PROXY_ADMIN_ZERO");
        require(newAdmin != address(_implementation.owner()), "ERROR:PXA-031:PROXY_ADMIN_SAME_AS_IMPLEMENTATION_OWNER");
        _proxy.changeAdmin(newAdmin);
    }


    function getImplementation() external view returns(VersionedOwnable) {
        return _implementation;
    }


    function getProxy() external view returns(TransparentUpgradeableProxy) {
        return _proxy;
    }
}
