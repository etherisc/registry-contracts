// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {NftId, toNftId} from "../registry/IChainNft.sol";

import {IInstance, IComponent, IComponentOwnerService} from "./IServices.sol";
import {Instance} from "./Instance.sol";


contract Product is IComponent {

    IInstance private _instance;

    address private _deployer;
    NftId private _nftId;
    string private _name;

    constructor(IInstance instance, string memory productName) {
        _instance = instance;
        _deployer = msg.sender;
        _name = productName;
    }

    function register() external {
        IComponentOwnerService service = _instance.getComponentOwnerService();
        _nftId = service.register(_instance, IComponent(this));
    }

    function name() external override view returns(string memory) {
        return _name;
    }

    function componentType() external override pure returns(ComponentType) {
        return ComponentType.Product;
    }

    function deployer() external override view returns(address) {
        return _deployer;
    }

    function nftId() external override view returns(NftId id) {
        return _nftId;
    }

    function owner() external override view returns(address) {
        return _instance.owner(_nftId);
    }

}