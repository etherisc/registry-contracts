// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

interface IComponent {

    enum CType {
        Undefined,
        Product,
        Oracle,
        Riskpool
    }

    enum CState {
        Undefined,
        Active,
        Locked
    }

    struct ComponentInfo {
        uint256 id;
        address cAddress;
        CType cType;
        CState state;
    }
}


interface IComponentContract is IComponent {

    function register()
        external
        returns(uint256 componentId);

    function getId() external view returns(uint256 id);
    function getType() external view returns(CType cType);
    function getInstanceAddress() external view returns(address instance);

}


interface IComponentOwnerServiceNext {

    function register(
        IComponentModule module, 
        IComponentContract component
    )
        external
        returns(uint256 id);
    
    function lock(
        IComponentModule module, 
        uint256 id
    )
        external;
    
    function unlock(
        IComponentModule module, 
        uint256 id
    )
        external;
}


interface IComponentModule is IComponent {

    function setComponentInfo(ComponentInfo memory info)
        external
        returns(uint256 componentId);

    function getComponentInfo(uint256 id)
        external
        view
        returns(ComponentInfo memory info);

    function getComponentId(address componentAddress)
        external
        view
        returns(uint256 id);

    function getComponentId(uint256 idx)
        external
        view
        returns(uint256 id);

    function components()
        external
        view
        returns(uint256 numberOfCompnents);

    function getComponentOwnerService()
        external
        view
        returns(IComponentOwnerServiceNext);
}