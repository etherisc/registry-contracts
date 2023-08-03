from brownie.network import accounts
from brownie.network.account import Account

from brownie import (
    interface,
    history,
    network,
    web3,
    ChainNft,
    ChainRegistry,
    ComponentOwnerService,
    Instance,
    Product,
)

from scripts.util import (
    contract_from_address,
    get_package,
    unix_timestamp,
    wait_for_confirmations,
)


def help():
    print('from scripts.util import contract_from_address')
    print('from scripts.deploy_experiment import all_in_1, help')
    print('(nft, registry, chhain_id, instance, product, component_owner_service, registry_owner, instance_owner, product_owner) = all_in_1(accounts)')
    print('')
    print('instance.nftId()')
    print('product.nftId()')
    print('')
    print('registry.objects(registry.chainId(), registry.INSTANCE())')
    print('registry.objects(registry.chainId(), registry.PRODUCT())')
    print('')
    print('info = registry.getNftInfo(instance.nftId()).dict()')
    print('idata = registry.decodeInstanceData(instance.nftId()).dict()')
    print('pdata = registry.decodeInstanceData(product.nftId()).dict()')


def all_in_1(
    accounts
):
    registry_owner = accounts[0]
    instance_owner = accounts[1]
    product_owner = accounts[2]

    # deploy and setup registry
    registry = ChainRegistry.deploy({'from': registry_owner})
    nft = ChainNft.deploy(registry, {'from': registry_owner})
    registry.setNftContract(nft, registry_owner, {'from': registry_owner})

    # setup modules
    component_owner_service = ComponentOwnerService.deploy({'from': registry_owner})

    # deploy and register new instance
    instance = Instance.deploy(
        registry, 
        component_owner_service, 
        {'from': instance_owner})

    instance.register("First Instance", {'from': instance_owner})

    # deploy and register product
    product = Product.deploy(instance, "First Product", {'from': product_owner})
    product.register({'from': product_owner})

    return (
        nft,
        registry,
        registry.chainId(),
        instance,
        product,
        component_owner_service,
        registry_owner,
        instance_owner,
        product_owner
    )
