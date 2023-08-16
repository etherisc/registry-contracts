// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {NftId} from "../registry/IChainNft.sol";
import {ObjectType} from "./ChainRegistry.sol";

interface IRegisterableOld {

    struct RegisterableInfo {
        NftId id;
        ObjectType objectType;
        string uri;
        bytes data;
        address deployer;
    }

    function isRegisterable() external pure returns(bool);
    function getInfo() external view returns(RegisterableInfo memory);

    function id() external view returns(NftId);
    function objectType() external view returns(ObjectType);
    function uri() external view returns(string memory);
    function data() external view returns(bytes memory);
    function deployer() external view returns(address);
}