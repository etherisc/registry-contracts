import pytest

from brownie import (
    interface,
    Wei,
    Contract,
    USD1,
    USD2,
    USD3,
    DIP,
    MockInstance,
    MockRegistry,
    UFixedMathTest,
    BaseTypes,
    Versionable,
    OwnableProxyAdmin,
    ChainNft,
    ChainRegistryV01,
    ChainRegistryV02,
    StakingV01,
)

from brownie.network import accounts
from brownie.network.account import Account

from scripts.const import (
    ACCOUNTS_MNEMONIC,
    INSTANCE_OPERATOR,
    INSTANCE_WALLET,
    ORACLE_PROVIDER,
    CHAINLINK_NODE_OPERATOR,
    RISKPOOL_KEEPER,
    RISKPOOL_WALLET,
    INVESTOR,
    PRODUCT_OWNER,
    INSURER,
    CUSTOMER1,
    CUSTOMER2,
    REGISTRY_OWNER,
    STAKING_OWNER,
    PROXY_ADMIN_OWNER,
    STAKER1,
    STAKER2,
    OUTSIDER,
    GIF_ACTOR
)

from scripts.util import (
    get_account,
    get_package,
    contract_from_address,
)

from scripts.deploy_registry import deploy_proxy


INITIAL_ACCOUNT_FUNDING = '1 ether'


def get_filled_account(
    accounts,
    account_no,
    funding=INITIAL_ACCOUNT_FUNDING
) -> Account:
    owner = get_account(ACCOUNTS_MNEMONIC, account_no)
    accounts[account_no].transfer(owner, funding)
    return owner

# fixtures with `yield` execute the code that is placed before the `yield` as setup code
# and code after `yield` is teardown code. 
# See https://docs.pytest.org/en/7.1.x/how-to/fixtures.html#yield-fixtures-recommended
@pytest.fixture(autouse=True)
def run_around_tests():
    try:
        yield
        # after each test has finished, execute one trx and wait for it to finish. 
        # this is to ensure that the last transaction of the test is finished correctly. 
    finally:
        accounts[8].transfer(accounts[9], 1)
        # dummy_account = get_account(ACCOUNTS_MNEMONIC, 999)
        # execute_simple_incrementer_trx(dummy_account)

#=== access to gif-contracts contract classes  =======================#

@pytest.fixture(scope="module")
def gifi(): return get_package('gif-interface')

@pytest.fixture(scope="module")
def gif(): return get_package('gif-contracts')

#=== actor account fixtures  ===========================================#

@pytest.fixture(scope="module")
def instanceOperator(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[INSTANCE_OPERATOR])

@pytest.fixture(scope="module")
def instanceWallet(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[INSTANCE_WALLET])

@pytest.fixture(scope="module")
def riskpoolKeeper(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[RISKPOOL_KEEPER])

@pytest.fixture(scope="module")
def riskpoolWallet(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[RISKPOOL_WALLET])

@pytest.fixture(scope="module")
def investor(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[INVESTOR])

@pytest.fixture(scope="module")
def productOwner(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[PRODUCT_OWNER])

@pytest.fixture(scope="module")
def oracleProvider(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[ORACLE_PROVIDER])

@pytest.fixture(scope="module")
def customer(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[CUSTOMER1])

@pytest.fixture(scope="module")
def customer2(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[CUSTOMER2])

@pytest.fixture(scope="module")
def registryOwner(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[REGISTRY_OWNER])

@pytest.fixture(scope="module")
def stakingOwner(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[STAKING_OWNER])

@pytest.fixture(scope="module")
def staker(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[STAKER1])

@pytest.fixture(scope="module")
def staker2(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[STAKER2])

@pytest.fixture(scope="module")
def proxyAdminOwner(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[PROXY_ADMIN_OWNER])

@pytest.fixture(scope="module")
def theOutsider(accounts) -> Account:
    return get_filled_account(accounts, GIF_ACTOR[OUTSIDER])

#=== stable coin fixtures ============================================#

@pytest.fixture(scope="module")
def usd1(instanceOperator) -> USD1: return USD1.deploy({'from': instanceOperator})

@pytest.fixture(scope="module")
def usd2(instanceOperator) -> USD2: return USD2.deploy({'from': instanceOperator})

@pytest.fixture(scope="module")
def usd3(instanceOperator) -> USD3: return USD3.deploy({'from': instanceOperator})

@pytest.fixture(scope="module")
def dip(instanceOperator) -> DIP: return DIP.deploy({'from': instanceOperator})

#=== base contract fixtures ==================================================#

@pytest.fixture(scope="module")
def baseTypes(theOutsider) -> BaseTypes:
    return BaseTypes.deploy({'from': theOutsider})

@pytest.fixture(scope="module")
def versionable(theOutsider) -> Versionable:
    return Versionable.deploy({'from': theOutsider})

@pytest.fixture(scope="module")
def math(theOutsider) -> UFixedMathTest:
    return UFixedMathTest.deploy({'from': theOutsider})

#=== chain registry fixtures ==================================================#

@pytest.fixture(scope="module")
def chainNftStandalone(registryOwner) -> ChainNft:
    return ChainNft.deploy(registryOwner, {'from': registryOwner})

@pytest.fixture(scope="module")
def chainRegistryV01Implementation(theOutsider) -> ChainRegistryV01:
    return ChainRegistryV01.deploy({'from': theOutsider})

@pytest.fixture(scope="module")
def proxyAdmin(
    chainRegistryV01Implementation,
    registryOwner,
    proxyAdminOwner
) -> OwnableProxyAdmin:
    return deploy_proxy(chainRegistryV01Implementation, registryOwner, proxyAdminOwner)

@pytest.fixture(scope="module")
def chainRegistryV01(proxyAdmin, registryOwner) -> ChainRegistryV01:
    registry = contract_from_address(
        ChainRegistryV01, 
        proxyAdmin.getProxy())
    
    nft = ChainNft.deploy(registry, {'from': registryOwner})

    registry.setNftContract(nft, registryOwner, {'from': registryOwner})
    
    return registry

#=== staking fixtures ==================================================#

@pytest.fixture(scope="module")
def stakingV01Implementation(theOutsider) -> StakingV01:
    return StakingV01.deploy({'from': theOutsider})

@pytest.fixture(scope="module")
def stakingProxyAdmin(
    stakingV01Implementation,
    stakingOwner,
    proxyAdminOwner
) -> OwnableProxyAdmin:
    return deploy_proxy(stakingV01Implementation, stakingOwner, proxyAdminOwner)


@pytest.fixture(scope="module")
def stakingV01(
    stakingProxyAdmin, 
    stakingOwner, 
    dip,
    chainRegistryV01,
    registryOwner
) -> StakingV01:
    staking = contract_from_address(
        StakingV01, 
        stakingProxyAdmin.getProxy())

    chainRegistryV01.setStakingContract(
        staking,
        {'from': registryOwner})

    staking.setDipContract(
        dip,
        {'from': stakingOwner})

    staking.setRegistry(
        chainRegistryV01,
        {'from': stakingOwner})

    return staking

#=== gif instance fixtures ====================================================#

@pytest.fixture(scope="module")
def mockInstance(instanceOperator) -> MockInstance: 
    return MockInstance.deploy({'from': instanceOperator})

@pytest.fixture(scope="module")
def mockRegistry(mockInstance): 
    return contract_from_address(
        MockRegistry,
        mockInstance.getRegistry())

# @pytest.fixture(scope="module")
# def instanceService(instance): return instance.getInstanceService()

#=== stable coin fixtures ============================================#

# @pytest.fixture(scope="module")
# def token(instanceOperator) -> CONTRACT_CLASS_TOKEN: return CONTRACT_CLASS_TOKEN.deploy({'from': instanceOperator})
