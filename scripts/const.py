# === GIF platform ========================================================== #

DIP_MAINNET_ADDRESS = '0xc719d010B63E5bbF2C0551872CD5316ED26AcD83'
USDT_MAINNET_ADDRESS = '0xdAC17F958D2ee523a2206206994597C13D831ec7'

# GIF release
GIF_RELEASE = '2.0.0'

# GIF modules
ACCESS_NAME = 'Access'
BUNDLE_NAME = 'Bundle'
COMPONENT_NAME = 'Component'

REGISTRY_CONTROLLER_NAME = 'RegistryController'
REGISTRY_NAME = 'Registry'

ACCESS_CONTROLLER_NAME = 'AccessController'
ACCESS_NAME = 'Access'

LICENSE_CONTROLLER_NAME = 'LicenseController'
LICENSE_NAME = 'License'

POLICY_CONTROLLER_NAME = 'PolicyController'
POLICY_NAME = 'Policy'

POLICY_DEFAULT_FLOW_NAME = 'PolicyDefaultFlow'
POOL_NAME = 'Pool'

QUERY_NAME = 'Query'

RISKPOOL_CONTROLLER_NAME = 'RiskpoolController'
RISKPOOL_NAME = 'Riskpool'
TREASURY_NAME = 'Treasury'

# GIF services
COMPONENT_OWNER_SERVICE_NAME = 'ComponentOwnerService'
PRODUCT_SERVICE_NAME = 'ProductService'
RISKPOOL_SERVICE_NAME = 'RiskpoolService'
ORACLE_SERVICE_NAME = 'OracleService'
INSTANCE_OPERATOR_SERVICE_NAME = 'InstanceOperatorService'
INSTANCE_SERVICE_NAME = 'InstanceService'

# GIF ecosystem actors
INSTANCE_OPERATOR = 'instanceOperator'
INSTANCE_WALLET = 'instanceWallet'
ORACLE_PROVIDER = 'oracleProvider'
CHAINLINK_NODE_OPERATOR = 'chainlinkNodeOperator'
RISKPOOL_KEEPER = 'riskpoolKeeper'
RISKPOOL_WALLET = 'riskpoolWallet'
INVESTOR = 'investor'
PRODUCT_OWNER = 'productOwner'
INSURER = 'insurer'
CUSTOMER1 = 'customer1'
CUSTOMER2 = 'customer2'
REGISTRY_OWNER = 'registryOwner'
PROXY_ADMIN_OWNER = 'proxyAdminOwner',
STAKING_OWNER = 'stakingOwner'
STAKER1 = 'staker1'
STAKER2 = 'staker2'
OUTSIDER = 'outsider'

GIF_ACTOR = {
    INSTANCE_OPERATOR: 0,
    INSTANCE_WALLET: 1,
    ORACLE_PROVIDER: 2,
    CHAINLINK_NODE_OPERATOR: 3,
    RISKPOOL_KEEPER: 4,
    RISKPOOL_WALLET: 5,
    INVESTOR: 6,
    PRODUCT_OWNER: 7,
    INSURER: 8,
    CUSTOMER1: 9,
    CUSTOMER2: 10,
    REGISTRY_OWNER: 14,
    PROXY_ADMIN_OWNER: 15,
    STAKING_OWNER: 16,
    STAKER1: 17,
    STAKER2: 18,
    OUTSIDER: 19,
}

# === GIF testing =========================================================== #

# ZERO_ADDRESS = accounts.at('0x0000000000000000000000000000000000000000')
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
COMPROMISED_ADDRESS = '0x0000000000000000000000000000000000000013'

# TEST account values
ACCOUNTS_MNEMONIC = 'candy maple cake sugar pudding cream honey rich smooth crumble sweet treat'


# TEST oracle/rikspool/product values
PRODUCT_NAME = 'Test.Product'
RISKPOOL_NAME = 'Test.Riskpool'
ORACLE_NAME = 'Test.Oracle'
ORACLE_INPUT_FORMAT = '(bytes input)'
ORACLE_OUTPUT_FORMAT = '(bool output)'
