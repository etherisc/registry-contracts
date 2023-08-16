import pytest
import brownie

from brownie import(
    accounts,
    interface,
    AccessOwnerService,
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


def test_setup(
    registryOwner,
    instanceOperator,
    productOwner
):
    registry = deploy_registry(registryOwner)
    instance = deploy_instance(registry, instanceOperator)
    product = deploy_product(instance, productOwner)

    instance_id = 1 # exoecgted instance id
    instance_type = registry.INSTANCE()

    product_id = 2 # expected product id
    product_type = registry.PRODUCT() # expected component type

    state_active = 1
    state_locked = 2

    assert instance.getComponentId['address'](product) == product_id

    assert product.getId() == product_id
    assert product.getType() == product_type
    assert product.getInstanceAddress() == instance

    info = instance.getComponentInfo(product_id).dict()
    assert info['id'] == product_id
    assert info['cAddress'] == product
    assert info['cType'] == product_type
    assert info['state'] == state_active

    component_owner_service = contract_from_address(interface.IComponentOwnerServiceNext, instance.getComponentOwnerService())
    component_owner_service.lock(instance, product_id, {'from': productOwner})

    info2 = instance.getComponentInfo(product_id).dict()
    assert info2['id'] == product_id
    assert info2['state'] == state_locked

    assert False


def deploy_instance(registry, instance_owner) -> InstanceNext:
    access_owner_service = AccessOwnerService.deploy({'from': instance_owner})
    component_owner_service = ComponentOwnerServiceNext.deploy({'from': instance_owner})

    instance = InstanceNext.deploy(
        registry,
        access_owner_service,
        component_owner_service, 
        {'from': instance_owner})

    instance.register({'from': instance_owner})

    return instance


def deploy_product(instance, product_owner) -> ProductNext:
    product = ProductNext.deploy(instance, {'from': product_owner})
    product.register({'from': product_owner})

    return product


def deploy_registry(registry_owner) -> Registry:
    registry = Registry.deploy({'from': registry_owner})

    return registry


def get_instance_owner():
    return accounts[0]