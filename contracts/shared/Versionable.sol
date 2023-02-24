// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "@openzeppelin-upgradeable/contracts/utils/StringsUpgradeable.sol";

import "./BaseTypes.sol";

contract Versionable is
    BaseTypes
{
    using StringsUpgradeable for uint16; 

    struct VersionInfo {
        Version version;
        string versionString;
        address implementation;
        address activatedBy; // tx.origin
        Blocknumber activatedIn;
        Timestamp activatedAt;
    }

    event LogVersionableActivated(Version version, address implementation, address activatedBy);

    mapping(Version version => VersionInfo info) private _versionHistory;
    Version [] private _versions;


    // controlled activation for controller contract
    constructor() {
        _activate(address(this));
    }

    // IMPORTANT this function needs to be implemented by each new version
    // and needs to call internal function call _activate() 
    function activate(address implementation)
        external 
        virtual
    { 
        _activate(implementation);
    }


    // can only be called once per contract
    // needs bo be called inside the proxy upgrade tx
    function _activate(
        address implementation
    )
        internal
    {
        address activatedBy = tx.origin;
        Version thisVersion = version();

        require(
            !isActivated(thisVersion),
            "ERROR:VRN-001:VERSION_ALREADY_ACTIVATED"
        );
        
        // require increasing version number
        if(_versions.length > 0) {
            Version lastVersion = _versions[_versions.length - 1];
            require(
                versionsAreIncreasing(lastVersion, thisVersion),
                "ERROR:VRN-002:VERSION_NOT_INCREASING"
            );
        }

        // update version history
        _versions.push(thisVersion);
        _versionHistory[thisVersion] = VersionInfo(
            thisVersion,
            toString(thisVersion),
            implementation,
            activatedBy,
            blockNumber(),
            blockTimestamp()
        );

        emit LogVersionableActivated(thisVersion, implementation, activatedBy);
    }


    function isActivated(Version _version) public view returns(bool) {
        return toInt(_versionHistory[_version].activatedIn) > 0;
    }


    // returns current version (ideally immutable)
    function version() public virtual pure returns(Version) {
        return toVersion(toPart(0), toPart(0), toPart(0));
    }


    function versions() external view returns(uint256) {
        return _versions.length;
    }


    function getVersion(uint256 idx) external view returns(Version) {
        require(idx < _versions.length, "ERROR:VRN-010:INDEX_TOO_LARGE");
        return _versions[idx];
    }


    function getVersionInfo(Version _version) external view returns(VersionInfo memory) {
        require(isActivated(_version), "ERROR:VRN-020:VERSION_UNKNOWN");
        return _versionHistory[_version];
    }


    function versionsAreIdentical(
        Version versionA,
        Version versionB
    )
        public
        pure
        returns(bool)
    {
        return toInt(versionA) == toInt(versionB);
    }


    function versionsAreIncreasing(
        Version oldVersion,
        Version newVersion
    )
        public
        pure
        returns(bool)
    {
        return toInt(oldVersion) < toInt(newVersion);
    }


    function toVersion(
        VersionPart major,
        VersionPart minor,
        VersionPart patch
    )
        public
        pure
        returns(Version)
    {
        uint majorInt = toInt(major);
        uint minorInt = toInt(minor);
        uint patchInt = toInt(patch);

        return Version.wrap(
            uint48(
                (majorInt << 32) + (minorInt << 16) + patchInt));
    }

    function toString(Version _version)
        public
        pure
        returns(string memory versionString)
    {
        (
            VersionPart major,
            VersionPart minor,
            VersionPart patch
        ) = toVersionParts(_version);

        return string(
            abi.encodePacked(
                "v", toString(major),
                ".", toString(minor),
                ".", toString(patch)));
    }


    function toString(VersionPart part) public pure returns(string memory partString) {
        uint16 partInt = VersionPart.unwrap(part);
        return StringsUpgradeable.toString(partInt);
    }


    function toVersionParts(Version _version)
        public
        pure
        returns(
            VersionPart major,
            VersionPart minor,
            VersionPart patch
        )
    {
        uint versionInt = toInt(_version);
        uint16 majorInt = uint16(versionInt >> 32);

        versionInt -= majorInt << 32;
        uint16 minorInt = uint16(versionInt >> 16);
        uint16 patchInt = uint16(versionInt - (minorInt << 16));

        return (
            toPart(majorInt),
            toPart(minorInt),
            toPart(patchInt)
        );
    }


    function toPart(uint16 versionPart)
        public
        pure
        returns(VersionPart)
    {
        return VersionPart.wrap(versionPart);
    }
}