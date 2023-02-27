// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "../shared/UFixedMath.sol";

contract UFixedMathTest is UFixedBase {

    function add(UFixed a, UFixed b) external pure returns(UFixed) {
        return a + b;
    }

    function sub(UFixed a, UFixed b) external pure returns(UFixed) {
        return a - b;
    }

    function dlt(UFixed a, UFixed b) external pure returns(UFixed) {
        return delta(a, b);
    }

    function mul(UFixed a, UFixed b) external pure returns(UFixed) {
        return a * b;
    }

    function div(UFixed a, UFixed b) external pure returns(UFixed) {
        return a / b;
    }

    function eq(UFixed a, UFixed b) external pure returns(bool) {
        return a == b;
    }

    function gt(UFixed a, UFixed b) external pure returns(bool) {
        return a > b;
    }

    function gtzUFixed(UFixed a) external pure returns(bool) {
        return gtz(a);
    }

    function eqzUFixed(UFixed a) external pure returns(bool) {
        return eqz(a);
    }

    function multiplier() external pure returns(uint256) {
        return 10 ** decimals();
    }

    // solidity testing
    function zero() internal pure returns(UFixed) { return itof(0); }
    function one() internal pure returns(UFixed) { return itof(1); }
    function two() internal pure returns(UFixed) { return itof(2); }
    function fortyTwo() internal pure returns(UFixed) { return itof(42); }

    function epsilon(uint256 n) public pure returns(UFixed) { return itof(1) / itof(n); }

    function testFrac(uint256 n) external pure returns(string memory) {
        UFixed oneHalf = itof(1) / itof(2);
        UFixed oneThird = itof(1) / itof(3);
        UFixed oneSixth = itof(1) / itof(6);

        assert(oneSixth - (oneHalf * oneThird) < epsilon(n));

        return "success";
    }

    function testAdd() external pure returns(string memory) {
        assert(zero() + zero() == zero());
        assert(zero() + one() == one());
        assert(one() + zero() == one());
        assert(one() + one() == two());

        assert(itof(40) + two() == fortyTwo());

        return "success";
    }

    function testSub() external pure returns(string memory) {
        assert(zero() - zero() == zero());
        assert(one() - zero() == one());
        assert(one() - one() == zero());
        assert(two() - zero() == two());
        assert(two() - one() == one());
        assert(two() - two() == zero());

        return "success";
    }
}