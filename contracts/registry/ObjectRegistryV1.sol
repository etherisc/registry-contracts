// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "@openzeppelin-upgradeable/contracts/utils/StringsUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/access/OwnableUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";

import "../shared/VersionedOwnable.sol";

type NftType is uint8;

contract ObjectRegistryV1 is
    ERC721EnumerableUpgradeable,
    VersionedOwnable
{
    using StringsUpgradeable for uint;
    using StringsUpgradeable for address;

    string public constant NAME = "Dezentralized Insurance Protocol Registry";
    string public constant SYMBOL = "DIPR";
    
    NftType public constant UNDEFINED = NftType.wrap(0);
    NftType public constant PROTOCOL = NftType.wrap(1);
    NftType public constant REGISTRY = NftType.wrap(2);

    NftType public constant INSTANCE = NftType.wrap(10);
    NftType public constant PRODUCT = NftType.wrap(11);
    NftType public constant ORACLE = NftType.wrap(12);
    NftType public constant RISKPOOL = NftType.wrap(13);
    NftType public constant BUNDLE = NftType.wrap(14);
    NftType public constant POLICY = NftType.wrap(15);

    NftType public constant STAKE = NftType.wrap(100);

    mapping(uint256 tokenId => Blocknumber number) private _mintedIn;
    mapping(uint256 tokenId => bytes data) private _data;
    mapping(uint256 tokenId => NftType t) private _type;

    mapping(NftType t => bool isSupported) private _typeIsSupported;

    uint256 private _chainId;

    uint256 private _idNext;
    string private _baseDid;


    // IMPORTANT 1. version needed for upgradable versions
    // _activate is using this to check if this is a new version
    // and if this version is higher than the last activated version
    function version() public override virtual pure returns(Version) {
        return toVersion(toPart(0), toPart(0), toPart(1));
    }

    // IMPORTANT 2. activate implementation needed
    // is used by proxy admin in its upgrade function
    function activate(address implementation) external override virtual { 
        _activate(implementation);

        // set main internal variables
        _chainId = block.chainid;
        _idNext = 1;
        _baseDid = string(abi.encodePacked("did:nft:eip155:", _chainIdAsStr(), "_erc721:", _addressAsStr(), "_"));

        // mint dip protocol on mainnet
        if(_chainId == 1) {
            _typeIsSupported[PROTOCOL] = true;
            _safeMintObject(owner(), PROTOCOL, "");
            _typeIsSupported[PROTOCOL] = false;
        } else {
            // skip 1st id if we're not on mainnet
            _idNext++;
        }

        // mint this registry
        bytes memory data = encodeRegistryData(block.chainid);
        _typeIsSupported[REGISTRY] = true;
        _safeMintObject(owner(), REGISTRY, data);
    }


    function getToken(uint256 tokenId)
        external 
        view 
        returns(
            string memory uri,
            address owner,
            NftType t,
            bytes memory data,
            Blocknumber mintedIn
        )
    {
        return (
            tokenURI(tokenId),
            ownerOf(tokenId),
            _type[tokenId],
            _data[tokenId],
            _mintedIn[tokenId]
        );
    }

    function encodeRegistryData(uint256 chainId) public pure returns(bytes memory data) { return abi.encode(chainId); }
    function decodeRegistryData(bytes memory data) external pure returns(uint256 chainId) { return abi.decode(data, (uint256)); }

    function toNftType(uint256 t) public pure returns(NftType) { return NftType.wrap(uint8(t)); }


    function _safeMintObject(address to, NftType t, bytes memory data) 
        internal 
        returns(uint256 tokenId)
    {
        require(_typeIsSupported[t], "OBJECT_TYPE_NOT_SUPPORTED");

        // enforce uniqe token ids over all chain id
        tokenId = _chainId * _idNext;
        _safeMint(to, tokenId);

        // store data if provided        
        if(data.length > 0) {
            _data[tokenId] = data;
        }

        // remember in which block the token was minted
        _type[tokenId] = t;
        _mintedIn[tokenId] = blockNumber();

        _idNext++;
    }


    // // TODO not yet sure this is needed
    // function _objectHash(NftType t, bytes memory data) internal pure returns(bytes32 objectHash) {
    //     return keccak256(abi.encodePacked(t, data));
    // }


    // retr
    function _baseURI() internal override view virtual returns (string memory) {
        return _baseDid;
    }

    function _chainIdAsStr() internal view returns(string memory) {
        return StringsUpgradeable.toString(block.chainid);
    }

    function _addressAsStr() internal view returns(string memory) {
        return StringsUpgradeable.toHexString(address(this));
    }
}
