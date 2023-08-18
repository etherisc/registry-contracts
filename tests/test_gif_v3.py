import pytest
import brownie

from brownie import(
    accounts,
    interface,
    ComponentOwnerServiceNext,
    InstanceNext,
    ProductNext,
    Registry
)

from scripts.util import contract_from_address


# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_deploy_explicit(
    registryOwner,
    instanceOperator,
    productOwner
):
    # renamings
    registry_owner = registryOwner
    instance_owner = instanceOperator
    product_owner = productOwner

    # deploy registry
    registry = Registry.deploy({'from': registry_owner})

    # deploy services (stateless)
    component_owner_service = ComponentOwnerServiceNext.deploy({'from': instance_owner})

    # deploy and register instance
    instance = InstanceNext.deploy(registry, component_owner_service, {'from': instance_owner})
    instance.register({'from': instance_owner})

    # grant product owner role
    product_owner_role = instance.getRoleForName('ProductOwner')
    instance.grantRole(product_owner_role, product_owner, {'from': instance_owner})

    # deploy product
    product = ProductNext.deploy(instance, {'from': product_owner})

    # register product
    component_owner_service.register(product, {'from': product_owner})

    # check outcome
    instance_id = 1 # expecgted instance id
    product_id = 2 # expected product id

    assert registry.getNftId(instance) == instance_id
    assert registry.getNftId(product) == product_id

    assert instance.getNftId() == instance_id
    assert instance.getType() == registry.INSTANCE()

    assert product.getNftId() == product_id
    assert product.getType() == registry.PRODUCT()
    assert product.getInstance() == instance


def test_deploy_simple(
    registryOwner,
    instanceOperator,
    productOwner
):
    # renamings
    registry_owner = registryOwner
    contract_owner = registryOwner
    instance_owner = instanceOperator
    product_owner = productOwner

    # deploy registry and services (1x per chain)
    registry = deploy_registry(registry_owner)
    services = deploy_services(contract_owner)

    # deploy instance and product(s) (1x per instance, 1x per product)
    instance = deploy_instance(registry, services, instance_owner)
    product = deploy_product(instance, product_owner)

    # check outcome
    instance_id = 1 # expecgted instance id
    product_id = 2 # expected product id

    assert registry.getNftId(instance) == instance_id
    assert registry.getNftId(product) == product_id

    assert instance.getNftId() == instance_id
    assert instance.getType() == registry.INSTANCE()

    assert product.getNftId() == product_id
    assert product.getType() == registry.PRODUCT()
    assert product.getInstance() == instance

    # info = instance.getComponentInfo(product_id).dict()
    # assert info['id'] == product_id
    # assert info['cAddress'] == product
    # assert info['cType'] == registry.PRODUCT()
    # assert info['state'] == state_active

    # component_owner_service = contract_from_address(interface.IComponentOwnerServiceNext, instance.getComponentOwnerService())
    # component_owner_service.lock(instance, product_id, {'from': productOwner})

    # info2 = instance.getComponentInfo(product_id).dict()
    # assert info2['id'] == product_id
    # assert info2['state'] == state_locked


def deploy_registry(registry_owner) -> Registry:
    return Registry.deploy({'from': registry_owner})


def deploy_services(contract_owner) -> dict:
    component_owner_service = ComponentOwnerServiceNext.deploy({'from': contract_owner})

    return {
        'component_owner_service': component_owner_service,
    }


def deploy_instance(registry, services, instance_owner) -> InstanceNext:
    instance = InstanceNext.deploy(
        registry,
        services['component_owner_service'], 
        {'from': instance_owner})

    instance.register({'from': instance_owner})

    return instance


def deploy_product(instance, product_owner) -> ProductNext:
    # deploy product
    product = ProductNext.deploy(instance, {'from': product_owner})

    # grant product owner role
    product_owner_role = instance.getRoleForName('ProductOwner')
    instance.grantRole(product_owner_role, product_owner, {'from': instance.getOwner()})

    # register product
    component_owner_service = contract_from_address(interface.IComponentOwnerServiceNext, instance.getComponentOwnerService())
    component_owner_service.register(product, {'from': product_owner})

    return product
