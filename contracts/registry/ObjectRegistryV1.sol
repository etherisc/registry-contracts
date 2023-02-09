// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

import "@openzeppelin-upgradeable/contracts/utils/StringsUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/access/OwnableUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";

import "../shared/BaseTypes.sol";

type NftType is uint16;

contract ObjectRegistryV1 is
    ERC721EnumerableUpgradeable,
    BaseTypes,
    OwnableUpgradeable
{
    using StringsUpgradeable for uint;
    using StringsUpgradeable for address;

    string public constant NAME = "Dezentralized Insurance Protocol Registry";
    string public constant SYMBOL = "DIPR";
    
    NftType public constant UNDEFINED = NftType.wrap(0);
    NftType public constant PROTOCOL = NftType.wrap(100);
    NftType public constant REGISTRY = NftType.wrap(101);

    NftType public constant INSTANCE = NftType.wrap(200);
    NftType public constant PRODUCT = NftType.wrap(201);
    NftType public constant ORACLE = NftType.wrap(202);
    NftType public constant RISKPOOL = NftType.wrap(203);
    NftType public constant BUNDLE = NftType.wrap(204);
    NftType public constant POLICY = NftType.wrap(205);

    NftType public constant STAKE = NftType.wrap(300);

    mapping(uint256 tokenId => Blocknumber number) private _mintedIn;
    mapping(uint256 tokenId => bytes data) private _data;
    mapping(uint256 tokenId => NftType t) private _type;

    mapping(NftType t => bool isSupported) private _typeIsSupported;

    uint256 private _chainId;
    uint256 private _version;

    uint256 private _idNext;
    string private _baseDid;

    // https://docs.openzeppelin.com/upgrades-plugins/1.x/writing-upgradeable
    constructor() {
            _disableInitializers();
    }

    // IMPORTANT initilizeer for upgradable logig
    function initialize() public virtual initializer {
        __ERC721_init(NAME, SYMBOL);
        __Ownable_init();

        // version handling
        _version = 0;
        _increaseVersion();

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

    function tryToIncreaseVersion() public returns(uint256) {
        _increaseVersion();
        return _version;
    }

    function version() public view returns(uint256) { return _version; }

    function getToken(uint256 tokenId)
        external 
        view 
        returns(
            string memory uri,
            address owner,
            NftType t,
            bytes memory data,
            Blocknumber mintedInBlock
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

    function toNftType(uint256 t) public pure returns(NftType) { return NftType.wrap(uint16(t)); }

    function _increaseVersion() internal onlyInitializing {
        _version += 1;
    }

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
