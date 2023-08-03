// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;


import {IChainNft, NftId, toNftId} from "../registry/IChainNft.sol";

import {IInstance, IComponent, IComponentOwnerService} from "./IServices.sol";


contract ComponentOwnerService 
    is IComponentOwnerService 
{

    event LogComponentRegister(IComponent.ComponentInfo info);

    function register(
        IInstance instance, 
        IComponent component
    )
        external
        // override
        returns(NftId id)
    {
        IComponent.ComponentInfo memory info;
        info.componentAddress = address(component);
        info.componentType = component.componentType();
        info.state = IComponent.ComponentState.Created;
        info.name = component.name();

        emit LogComponentRegister(info);

        return instance.registerComponent(info, component.deployer());
    }


    function pause(
        IInstance instance, 
        NftId id
    )
        external
        // override
    {
        IComponent.ComponentInfo memory info = instance.getComponentInfo(id);
        info.state = IComponent.ComponentState.Paused;
        instance.setComponentInfo(info);
    }


    function resume(
        IInstance instance, 
        NftId id
    )
        external
        // override
    {
        IComponent.ComponentInfo memory info = instance.getComponentInfo(id);
        info.state = IComponent.ComponentState.Active;
        instance.setComponentInfo(info);
    }
}
