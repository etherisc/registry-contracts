// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {NftId} from "../registry/IChainNft.sol";
import {ObjectType} from "./ChainRegistry.sol";
import {IRegisterable} from "./IRegisterable.sol";


contract Registerable is IRegisterable {

    address private _deployer;
    ObjectType private _type;
    string private _uri;
    bytes private _data; 
    NftId private _id;

    constructor(
        ObjectType _objectType,
        string memory uriString,
        bytes memory dataBytes
    )
    {
        _type = _objectType;
        _deployer = msg.sender;

        if(bytes(uriString).length > 0) {
            _uri = uriString;
        }

        if(dataBytes.length > 0) {
            _data = dataBytes;
        }
    }

    function isRegisterable() external pure returns(bool) { return true; }

    function getInfo() external view returns(IRegisterable.RegisterableInfo memory) {
        return IRegisterable.RegisterableInfo(_id, _type, _uri, _data, _deployer);
    }

    function id() external override view returns(NftId) {
        return _id;
    }

    function objectType() external override view returns(ObjectType) {
        return _type;
    }

    function uri() external override view returns(string memory) {
        return _uri;
    }

    function data() external override view returns(bytes memory) {
        return _data;
    }

    function deployer() external override view returns(address) {
        return _deployer;
    }
}