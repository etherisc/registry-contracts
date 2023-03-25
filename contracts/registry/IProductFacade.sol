// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

/*
 *  @dev needs to be in sync with definition in DepegProduct
 */

import {IInstanceRegistryFacade} from "./IInstanceRegistryFacade.sol";
interface IProductFacade {

    function getRegistry() external view returns(IInstanceRegistryFacade);
    function getRiskpoolId() external view returns(uint256 riskpoolId);
    function getToken() external view returns(address token);
}