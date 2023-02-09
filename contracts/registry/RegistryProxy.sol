// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.18;

// import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/proxy/transparent/TransparentUpgradeableProxy.sol";

contract RegistryProxy is
    TransparentUpgradeableProxy
    // Ownable
{
    // corresponds to calling "initialize()" on the target contract
    bytes public constant INITIALIZER_CALL_SIGNATURE = "initialize()";
    bytes public constant INITIALIZER_CALL_DATA = abi.encode(bytes4(keccak256(bytes(INITIALIZER_CALL_SIGNATURE))));
    constructor(
        address logic // controller logic contract address
    )
        // Ownable(),
        TransparentUpgradeableProxy(
            logic, 
            msg.sender, // only account that will be able to upgrade
            INITIALIZER_CALL_DATA
        )
    { }
}
