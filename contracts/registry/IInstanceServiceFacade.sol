// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;


import "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";


// needs to be in sync with definition in IInstanceService
interface IInstanceServiceFacade {

    // needs to be in sync with definition in IComponent
    enum ComponentType {
        Oracle,
        Product,
        Riskpool
    }

    // needs to be in sync with definition in IComponent
    enum ComponentState {
        Created,
        Proposed,
        Declined,
        Active,
        Paused,
        Suspended,
        Archived
    }

    // needs to be in sync with definition in IBundle
    enum BundleState {
        Active,
        Locked,
        Closed,
        Burned
    }

    // needs to be in sync with definition in IBundle
    struct Bundle {
        uint256 id;
        uint256 riskpoolId;
        uint256 tokenId;
        BundleState state;
        bytes filter; // required conditions for applications to be considered for collateralization by this bundle
        uint256 capital; // net investment capital amount (<= balance)
        uint256 lockedCapital; // capital amount linked to collateralizaion of non-closed policies (<= capital)
        uint256 balance; // total amount of funds: net investment capital + net premiums - payouts
        uint256 createdAt;
        uint256 updatedAt;
    }

    function getChainId() external view returns(uint256 chainId);
    function getInstanceId() external view returns(bytes32 instanceId);
    function getInstanceOperator() external view returns(address instanceOperator);

    function getComponentType(uint256 componentId) external view returns(ComponentType componentType);
    function getComponentState(uint256 componentId) external view returns(ComponentState componentState);
    function getComponentToken(uint256 componentId) external view returns(IERC20Metadata token);

    function getBundle(uint256 bundleId) external view returns(Bundle memory bundle);
}