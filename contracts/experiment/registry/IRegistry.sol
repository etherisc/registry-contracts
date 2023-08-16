// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

interface IOwnable {
    function getOwner() external view returns(address owner);
}

interface IRegistryLinked {
    function setRegistry(address registry) external;
    function getRegistry() external view returns(IRegistry registry);
}

interface IRegisterable is 
    IOwnable,
    IRegistryLinked
{

    function register() external returns(uint256 id);
    
    function getId() external view returns(uint256 id);
    function getType() external view returns(uint256 objectType);
    function isRegisterable() external pure returns(bool);
    function getInitialOwner() external view returns(address initialOwner);

    function isRegistered() external view returns(bool);
}


interface IRegistry {

    struct RegistryInfo {
        uint256 id;
        uint256 objectType;
        address objectAddress;
        address initialOwner;
    }

    function INSTANCE() external pure returns(uint256);
    function PRODUCT() external pure returns(uint256);

    function register(address object) external returns(uint256 id);
    function transfer(uint256 id, address newOwner) external;

    function getId(address object) external view returns(uint256 id);
    function getInfo(uint256 id) external view returns(RegistryInfo memory info);
    function getOwner(uint256 id) external view returns(address);

    function isRegistered(address object) external view returns(bool);
}
