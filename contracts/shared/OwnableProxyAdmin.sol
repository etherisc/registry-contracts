// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/proxy/transparent/TransparentUpgradeableProxy.sol";

import "./VersionedOwnable.sol";

contract OwnableProxyAdmin is
    Ownable
{
    string public constant ACTIVATE_SIGNATURE = "activate(address)";
    string public constant ACTIVATE_AND_SET_OWNER_SIGNATURE = "activateAndSetOwner(address,address)";

    VersionedOwnable private _implementation;
    TransparentUpgradeableProxy private _proxy;

    constructor(
        VersionedOwnable implementation,
        address implementationOwner
    )
        Ownable()
    {
        require(address(implementation) != address(0), "ERROR:PXA-001:IMPLEMENTATION_ZERO");
        require(implementationOwner != address(0), "ERROR:PXA-002:IMPLEMENTATION_OWNER_ZERO");

        _proxy = new TransparentUpgradeableProxy(
            address(implementation), 
            address(this),
            abi.encodeWithSignature(
                ACTIVATE_AND_SET_OWNER_SIGNATURE,
                address(implementation),
                implementationOwner)
        );

        _implementation = implementation;
    }


    function upgrade(VersionedOwnable newImplementation) 
        external
        onlyOwner
    {
        require(address(newImplementation) != address(0), "ERROR:PXA-010:IMPLEMENTATION_ZERO");
        require(address(newImplementation) != address(_implementation), "ERROR:PXA-011:IMPLEMENTATION_NOT_NEW");

        _implementation = newImplementation;
        _proxy.upgradeToAndCall(
            address(newImplementation), 
            abi.encodeWithSignature(
                ACTIVATE_SIGNATURE,
                address(newImplementation))
        );
    }


    function transferAdmin(address newAdmin)
        external
        onlyOwner
    {
        require(newAdmin != address(0), "ERROR:PXA-020:PROXY_ADMIN_ZERO");
        require(newAdmin != address(_implementation.owner()), "ERROR:PXA-012:PROXY_ADMIN_SAME_AS_IMPLEMENTATION_OWNER");
        _proxy.changeAdmin(newAdmin);
    }


    function getImplementation() external view returns(VersionedOwnable) {
        return _implementation;
    }


    function getProxy() external view returns(TransparentUpgradeableProxy) {
        return _proxy;
    }
}
