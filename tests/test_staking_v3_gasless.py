import pytest
import brownie

from eip712_structs import EIP712Struct, Address, Bytes, String, Uint
from eip712_structs import make_domain
from eth_utils import big_endian_to_int
from coincurve import PrivateKey, PublicKey

from brownie.network.account import Account

from brownie import (
    chain,
    history,
    interface,
    web3,
    USD1,
    USD2,
    DIP,
    MockInstance,
    MockInstanceRegistry,
    OwnableProxyAdmin,
    ChainRegistryV01,
    StakingV01,
    StakingV03,
    StakingMessageHelper,
)

from web3 import Web3

from scripts.const import ZERO_ADDRESS
from scripts.util import (
    contract_from_address,
    s2b32,
    unix_timestamp
)

keccak_hash = lambda x : Web3.keccak(x)

# https://medium.com/treum_io/introducing-eip-712-structs-in-python-27eac7f38281
# https://gist.github.com/alexisrobert/9facb3d21d4f04946f3a41b5a3c0a9a1

# EIP712_STAKE_TYPE = "Stake(uint96 target,uint256 dipAmount,bytes32 signatureId)"
class Stake(EIP712Struct):
    target = Uint(96)
    dipAmount = Uint(256)
    signatureId = Bytes(32)

# EIP712_RESTAKE_TYPE = "Restake(uint96 oldTarget,uint96 newTarget,bytes32 signatureId)"
class Restake(EIP712Struct):
    stakeId = Uint(96)
    newTarget = Uint(96)
    signatureId = Bytes(32)


def create_stake_signature(target, dipAmount, signatureId, contractAddress, owner):
    # prepare messsage
    message = Stake()
    message['target'] = target
    message['dipAmount'] = dipAmount
    message['signatureId'] = signatureId

    stake_domain = make_domain(
        name='EtheriscStaking',
        version='1',
        chainId=web3.chain_id,
        verifyingContract=contractAddress)

    signable_bytes = message.signable_bytes(stake_domain)

    return calculate_signature(signable_bytes, owner)


def create_restake_signature(stakeId, newTarget, signatureId, contractAddress, owner):
    # prepare messsage
    message = Restake()
    message['stakeId'] = stakeId
    message['newTarget'] = newTarget
    message['signatureId'] = signatureId

    stake_domain = make_domain(
        name='EtheriscStaking',
        version='1',
        chainId=web3.chain_id,
        verifyingContract=contractAddress)

    signable_bytes = message.signable_bytes(stake_domain)

    return calculate_signature(signable_bytes, owner)


def calculate_signature(signable_bytes, owner):
    pk = PrivateKey.from_int(int(owner.private_key, 16))
    sig = pk.sign_recoverable(signable_bytes, hasher=keccak_hash)
    v = sig[64] + 27
    r = big_endian_to_int(sig[0:32])
    s = big_endian_to_int(sig[32:64])    

    signature_raw = r.to_bytes(32, 'big') + s.to_bytes(32, 'big') + v.to_bytes(1, 'big')
    signature = '0x{}'.format(signature_raw.hex())

    return signature


# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_signature_and_signer_for_staking(
        mockInstance,
        mockRegistry,
        usd2,
        dip,
        proxyAdmin,
        proxyAdminOwner,
        chainRegistryV01,
        registryOwner,
        theOutsider,
        messageHelper, 
        staker
):

    bundle_nft = create_mock_bundle_setup(
        mockInstance,
        mockRegistry,
        usd2,
        proxyAdmin,
        proxyAdminOwner,
        chainRegistryV01,
        registryOwner,
        theOutsider)

    # prepare staking parameters
    target = bundle_nft
    dipAmount = 10000 * 10**dip.decimals()
    signatureId = s2b32('some-unique-signature-id')

    signature = create_stake_signature(target, dipAmount, signatureId, messageHelper.address, staker)
    digest = messageHelper.getStakeDigest(target, dipAmount, signatureId)
    signer_from_signature = messageHelper.getSigner(digest, signature)

    assert signer_from_signature == staker

    # same assertion rerwitten
    assert staker == messageHelper.getSigner(digest, signature)

    # failure cases: any change in message digest attributes leads to an address that does not match the staker
    digest = messageHelper.getStakeDigest(target + 1, dipAmount, signatureId)
    assert staker != messageHelper.getSigner(digest, signature)

    digest = messageHelper.getStakeDigest(target, dipAmount + 1000 * 10**dip.decimals(), signatureId)
    assert staker != messageHelper.getSigner(digest, signature)

    digest = messageHelper.getStakeDigest(target, dipAmount, s2b32('some-other-signature'))
    assert staker != messageHelper.getSigner(digest, signature)


def test_signature_and_signer_for_restaking(
        mockInstance,
        mockRegistry,
        usd2,
        dip,
        proxyAdmin,
        proxyAdminOwner,
        chainRegistryV01,
        registryOwner,
        theOutsider,
        messageHelper, 
        staker
):
    # prepare re-staking parameters
    stakeId = 1234
    newTarget = 5678
    signatureId = s2b32('unique-restaking-id')

    signature = create_restake_signature(stakeId, newTarget, signatureId, messageHelper.address, staker)
    digest = messageHelper.getRestakeDigest(stakeId, newTarget, signatureId)

    # happy path case
    assert staker == messageHelper.getSigner(digest, signature)

    # failure cases: any change in message digest attributes leads to an address that does not match the staker
    digest = messageHelper.getRestakeDigest(stakeId + 1, newTarget, signatureId)
    assert staker != messageHelper.getSigner(digest, signature)

    digest = messageHelper.getRestakeDigest(stakeId, newTarget - 13, signatureId)
    assert staker != messageHelper.getSigner(digest, signature)

    digest = messageHelper.getRestakeDigest(stakeId, newTarget, s2b32('some-other-signature'))
    assert staker != messageHelper.getSigner(digest, signature)


def test_stake_bundle_gasless(
    mockInstance: MockInstance,
    mockRegistry: MockInstanceRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    dip: DIP,
    instanceOperator: Account,
    stakingV01: StakingV01,
    stakingOwner: Account,
    staker: Account,
    theOutsider: Account
):
    bundle_nft = create_mock_bundle_setup(
        mockInstance,
        mockRegistry,
        usd2,
        proxyAdmin,
        proxyAdminOwner,
        chainRegistryV01,
        registryOwner,
        theOutsider)
    
    assert bundle_nft > 0

    # setup up message helper
    messageHelper = StakingMessageHelper.deploy({'from': stakingOwner})

    with brownie.reverts():
        stakingV01.setMessageHelper(messageHelper, {'from': theOutsider})

    stakingV01.setMessageHelper(messageHelper, {'from': stakingOwner})
    assert stakingV01.getMessageHelperAddress() == messageHelper

    # attempt to stake
    staking_amount = 5000 * 10 ** dip.decimals()
    prepare_staker(staker, staking_amount, dip, instanceOperator, stakingV01)

    # check balances before staking
    assert dip.balanceOf(staker) == staking_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()) == 0

    signatureId = s2b32('some-unique-chars') # this can make the stake signature unique even when other stake attributes are used multiple times
    signature = create_stake_signature(bundle_nft, staking_amount, signatureId, stakingV01.getMessageHelperAddress(), staker)

    staking_tx = stakingV01.createStakeWithSignature(
        staker,
        bundle_nft,
        staking_amount,
        signatureId,
        signature,
        {'from': theOutsider })

    # check balances after staking
    assert dip.balanceOf(staker) == 0
    assert dip.balanceOf(stakingV01.getStakingWallet()) == staking_amount

    # check staking balance event
    assert 'LogStakingStaked' in staking_tx.events
    evt = staking_tx.events['LogStakingStaked']
    nft_id = evt['id']
    assert evt['target'] == bundle_nft
    assert evt['user'] == staker
    assert evt['amount'] == staking_amount
    assert evt['newBalance'] == staking_amount

    # check staking nft
    assert 'LogStakingNewStakeCreated' in staking_tx.events
    evt = staking_tx.events['LogStakingNewStakeCreated']
    assert evt['target'] == bundle_nft
    assert evt['user'] == staker
    assert evt['id'] == nft_id

    # check nft info in registry
    assert chainRegistryV01.ownerOf(nft_id) == staker

    state_approved = 2 # ObjectState { Undefined, Proposed, Approved, ...}
    info = chainRegistryV01.getNftInfo(nft_id).dict()
    assert info['id'] == nft_id
    assert info['objectType'] == chainRegistryV01.STAKE()
    assert info['state'] == state_approved
    assert info['version'] == chainRegistryV01.version()
    (target_id, target_type) = chainRegistryV01.decodeStakeData(nft_id)
    assert target_id == bundle_nft
    assert target_type == chainRegistryV01.BUNDLE()

    # check staking info for nft
    info = stakingV01.getInfo(nft_id).dict()
    block_timestamp = web3.eth.getBlock(web3.eth.block_number)['timestamp']
    assert info['id'] == nft_id
    assert info['target'] == bundle_nft
    assert info['stakeBalance'] == staking_amount
    assert info['rewardBalance'] == 0
    assert info['createdAt'] == block_timestamp
    assert info['updatedAt'] == block_timestamp
    assert info['version'] == stakingV01.version()


def test_restake_gasless(
    stakingProxyAdmin: OwnableProxyAdmin,
    mockInstance: MockInstance,
    mockRegistry: MockInstanceRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    dip: DIP,
    instanceOperator: Account,
    stakingV01: StakingV03,
    stakingOwner: Account,
    staker: Account,
    theOutsider: Account
):

    # setup up message helper
    messageHelper = StakingMessageHelper.deploy({'from': stakingOwner})
    stakingV01.setMessageHelper(messageHelper, {'from': stakingOwner})

    # registry = contract_from_address(ChainRegistryV01, stakingV01.getRegistry())

    # set default reward rate to 12.5%
    apr_12_5 = stakingV01.toRate(125, -3)
    stakingV01.setRewardRate(apr_12_5, {'from': stakingOwner})

    # provide some reward reserves
    reward_reserves_amount = 1000*10**dip.decimals()
    dip.approve(stakingV01, reward_reserves_amount, {'from': instanceOperator})
    stakingV01.refillRewardReserves(reward_reserves_amount, {'from': instanceOperator})

    bundle_lifetime = 100 * 24 * 3600
    bundle_nft = create_mock_bundle_setup(
        mockInstance,
        mockRegistry,
        usd2,
        proxyAdmin,
        proxyAdminOwner,
        chainRegistryV01,
        registryOwner,
        theOutsider,
        bundle_lifetime = bundle_lifetime)

    bundle_nft2 = create_mock_bundle_setup(
        mockInstance,
        mockRegistry,
        usd2,
        proxyAdmin,
        proxyAdminOwner,
        chainRegistryV01,
        registryOwner,
        theOutsider,
        bundle_lifetime = 2*bundle_lifetime,
        bundle_id = 2,
        is_first_bundle = False)
    
    assert bundle_nft > 0
    assert bundle_nft2 > 0
    assert bundle_nft != bundle_nft2

    # attempt to stake
    staking_amount = 5000 * 10 ** dip.decimals()
    prepare_staker(staker, 2 * staking_amount, dip, instanceOperator, stakingV01)

    # check balances before staking
    assert dip.balanceOf(staker) == 2 * staking_amount
    assert dip.balanceOf(stakingV01.getStakingWallet()) == reward_reserves_amount

    staking_tx = stakingV01.createStake(
        bundle_nft,
        staking_amount,
        {'from': staker })

    assert 'LogStakingNewStakeCreated' in staking_tx.events
    stake_id = staking_tx.events['LogStakingNewStakeCreated']['id']

    # get balances
    staking_balance1 = stakingV01.stakeBalance()
    reward_reserves1 = stakingV01.rewardReserves()
    total_balance1 = staking_balance1 + reward_reserves1
    wallet_balance1 = dip.balanceOf(stakingV01.getStakingWallet())
    assert total_balance1 == wallet_balance1

    sleep_time = bundle_lifetime + 1
    chain.sleep(sleep_time)
    chain.mine(1)

    info = stakingV01.getInfo(stake_id)
    stake_balance = info.dict()['stakeBalance']
    reward_balance = info.dict()['rewardBalance'] + stakingV01.calculateRewardsIncrement(info)
    restake_amount = stake_balance + reward_balance

    # gasless restaking
    signatureId = s2b32('unique-restake-chars') # this can make the restake signature unique even when other stake attributes are used multiple times
    signature = create_restake_signature(stake_id, bundle_nft2, signatureId, stakingV01.getMessageHelperAddress(), staker)

    restake_tx = stakingV01.restakeWithSignature(
        staker,
        stake_id, 
        bundle_nft2, 
        signatureId,
        signature,
        {'from': theOutsider})

    assert 'LogStakingRestaked' in restake_tx.events
    stake_id2 = restake_tx.events['LogStakingRestaked']['stakeId']

    # check that bundle stakes have been properly updated
    assert stakingV01.stakes(bundle_nft) == 0
    assert abs(stakingV01.stakes(bundle_nft2) - restake_amount)/10**dip.decimals() < 10**-4

    # get balances after restake
    staking_balance2 = stakingV01.stakeBalance()
    reward_reserves2 = stakingV01.rewardReserves()
    total_balance2 = staking_balance2 + reward_reserves2
    wallet_balance2 = dip.balanceOf(stakingV01.getStakingWallet())

    assert reward_reserves1 > reward_reserves2
    assert staking_balance1 < staking_balance2
    assert reward_reserves1 - reward_reserves2 == staking_balance2 - staking_balance1

    assert total_balance2 == wallet_balance2
    assert total_balance2 == total_balance1


def prepare_staker(
    staker,
    staking_amount,
    dip,
    instanceOperator,
    stakingV01
):
    dip.transfer(staker, staking_amount, {'from': instanceOperator })
    dip.approve(stakingV01.getStakingWallet(), staking_amount, {'from': staker })


def create_mock_bundle_setup(
    mockInstance: MockInstance,
    mockRegistry: MockInstanceRegistry,
    usd2: USD2,
    proxyAdmin: OwnableProxyAdmin,
    proxyAdminOwner: Account,
    chainRegistryV01: ChainRegistryV01,
    registryOwner: Account,
    theOutsider: Account,
    bundle_lifetime = 14 * 24 * 3600,
    bundle_id = 1,
    is_first_bundle = True
) -> int:
    # setup attributes
    chain_id = chainRegistryV01.toChain(mockInstance.getChainId())
    instance_id = mockInstance.getInstanceId()
    riskpool_id = 1
    bundle_name = 'my test bundle'
    bundle_funding = 10000 * 10 ** usd2.decimals()
    bundle_expiry_at = unix_timestamp() + bundle_lifetime

    # setup mock instance
    type_riskpool = 2

    state_created = 0
    state_active = 3
    state_paused = 4

    mockInstance.setComponentInfo(
        riskpool_id,
        type_riskpool,
        state_active,
        usd2)

    bundle_state_active = 0 # enum BundleState { Active, Locked, Closed, Burned }
    mockInstance.setBundleInfo(
        bundle_id,
        riskpool_id,
        bundle_state_active,
        bundle_funding)

    if is_first_bundle:
        # register token
        tx_token = chainRegistryV01.registerToken(
                chain_id,
                usd2,
                '',
                {'from': registryOwner})

        # register instance
        tx_instance = chainRegistryV01.registerInstance(
            mockRegistry,
            'mockRegistry TEST',
            '',
            {'from': registryOwner})

        # register riskpool
        tx_riskpool = chainRegistryV01.registerComponent(
            instance_id,
            riskpool_id,
            '',
            {'from': registryOwner})

    # register bundle
    tx_bundle = chainRegistryV01.registerBundle(
        instance_id,
        riskpool_id,
        bundle_id,
        bundle_name,
        bundle_expiry_at,
        {'from': theOutsider})

    nft_id = chainRegistryV01.getBundleNftId(instance_id, bundle_id)

    return nft_id
