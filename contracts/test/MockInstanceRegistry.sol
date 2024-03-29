// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import {IInstanceRegistryFacade} from "../registry/IInstanceRegistryFacade.sol";

contract MockInstanceRegistry is IInstanceRegistryFacade {

    address private _instanceService;

    function setInstanceServiceAddress(address instanceService) external {
        _instanceService = instanceService;
    }

    function getContract(bytes32 contractName)
        external
        view
        returns (address contractAddress)
    {
        require(contractName == bytes32("InstanceService"), "ERROR:DRG-001:CONTRACT_NOT_REGISTERED");
        return _instanceService;
    }
}
