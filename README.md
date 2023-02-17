![Build](https://github.com/etherisc/depeg-contracts/actions/workflows/build.yml/badge.svg)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![](https://dcbadge.vercel.app/api/server/cVsgakVG4R?style=flat)](https://discord.gg/Qb6ZjgE8)

# Decentralized Insurance Protocol Object Registry

This repository holds the smart contracts for the DIP registry.

## Object DID

Registered objects are represented by NFT that get unique identifiers.
A DID representation of the object is provided as URI.

Spec and example extracted from links below
```
spec    did:nft:{chainNamespace}:{chainReference}_erc721:{contractAddress}_{tokenId}
example did:nft:eip155:1_erc721:0x06012c8cf97BEaD5deAe237070F9587f8E7A266d_771769
```

External links regarding DID for NFT
* [Ceramic DID for NFT](https://github.com/ceramicnetwork/nft-did-resolver)
* [CAIP-22](https://github.com/ChainAgnostic/CAIPs/blob/master/CAIPs/caip-22.md)
* [CAIP-19](https://github.com/ChainAgnostic/namespaces/blob/main/eip155/caip19.md)

## Setup Assumptions

1. Developing with VS Code
2. Working with dev containers

## Technical links

https://github.com/briangershon/openzeppelin-erc721-upgradeable


## Chain Registry

### Sample Brownie Console Session

Start the console
```bash
brownie console
```

In the console play around with the upgradable demo contracts
```python
from scripts.util import contract_from_address

pao = accounts[0] # proxy admin owner
ro = accounts[1] # registry owner

a = accounts[10] # some random account

fpao = {'from':pao}
fro = {'from':ro}

# deploy the initial registry logic
r = ChainRegistryV01.deploy(fpao)

# deploy the proxy admin and provide the 
# registry implementation its initial owner
pa = OwnableProxyAdmin.deploy(r, ro, fpao)
p = contract_from_address(ChainRegistryV01, pa.getProxy())

# deploy the two next versions
i1 = DemoV1.deploy(fio)

## Upgradability with VersionedOwnable

VersionedOwnable: Base contract for versioned owned upgradable contracts. 
Versionable implements the activation logic that takes care of managing the version history
VersionedOwnable just adds ownability (OpenZeppelin) to Versionable.

Proxy deployment for upgradability of some contract based on VersionedOwnable is taken care of by OwnableProxyAdmin.
OwnableProxyAdmin is an ownable contract too and creates its own TransparentUpgradeableProxy (OpenZeppelin) contract inside.

The high level process works as follows:
1. deploy implementation contract (derived from VersionedOwnable)
1. deploy OwnableProxyAdmin providing implementation and owner of implementation as constructor arguments
1. work with the implementation trough the transparent proxy (OwnableProxyAdmin.getProxy)
1. deploy the next version newImplementation (derived from implementation)
1. upgrade the logic behind the proxy using OwnableProxyAdmin.upgrade(newImplementation)

After step 3 working with the initial upgradable contract is possible (using the proxy).
After step 5 working with the upgraded contract is possible (using the identical proxy as in step 3).
For further upgrades repeat steps 4 and 5.

### Sample Brownie Console Session

Start the console
```bash
brownie console
```

In the console play around with the upgradable demo contracts
```python
from scripts.util import contract_from_address

po = accounts[0]
io = accounts[1]

a = accounts[10]
b = accounts[11]
c = accounts[12]

fpo = {'from':po}
fio = {'from':io}

# deploy the initial logic implementation
i = VersionedOwnable.deploy(fio)

# deploy the proxy admin and provide the implementation and the initial owner for the implementation
pa = OwnableProxyAdmin.deploy(i, io, fpo)
p = contract_from_address(VersionedOwnable, pa.getProxy())

# deploy the two next versions
i1 = DemoV1.deploy(fio)
i2 = DemoV2.deploy(fio)

# upgrade the initial implementation to DemoV1
pa.upgrade(i1, fpo)
p = contract_from_address(DemoV1, pa.getProxy())
p.specialMessage()
p.upgradableDemo()
p.nonUpgradableDemo1()
# p.theValue() below fails as this function is not implemented in DemoV1
p.theValue()

# further upgrade the initial implementation to DemoV2
pa.upgrade(i2, fpo)
p = contract_from_address(DemoV2, pa.getProxy())
# p.theValue now works as it is implemented in DemoV2
p.theValue()
p.upgradableDemo()
p.specialMessage()
p.nonUpgradableDemo1()

# the call below fails as a is not the owner of the implementation
p.setSpecialMessage('something completeley different', {'from':a})
# the call below world as io is the implementatoin owner
p.setSpecialMessage('something completeley different', {'from':io})
p.specialMessage()

# show version history
p.versions()
# show the first deployed version
p.getVersionInfo(p.getVersion(0)).dict()

# show the full version history
list(map(lambda version: p.getVersionInfo(p.getVersion(version))[1:], range(p.versions())))
```

The version history should look like the following output
```python
[
    ('v0.0.0', '0xe7CB1c67752cBb975a56815Af242ce2Ce63d3113', '0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87', 2, 1675978743), 
    ('v1.0.0', '0xDA1C81E678CbafE8EF2cfa2eC9D8D7724bAA3DD2', '0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87', 5, 1675978752), 
    ('v1.1.0', '0xE92E591c9661fe380Bb0949D22d27432E9f5b7F6', '0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87', 6, 1675978780)
]
```

## Interaction via Command Line

### Running Unit Tests

```bash
brownie test -n 8
```

### Deploy and Verify with Ganache

```bash
brownie console
```
