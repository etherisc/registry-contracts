// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

type UFixed is uint256;

interface IUFixedMath {

    enum Rounding {
        Down, // floor(value)
        Up, // = ceil(value)
        HalfUp // = floor(value + 0.5)
    }

    function itof(uint256 a) external pure returns(UFixed af);
    function itof(uint256 a, int8 exp) external pure returns(UFixed af);

    function ftoi(UFixed af) external pure returns(uint256 a);
    function ftoi(UFixed af, Rounding rounding) external pure returns(uint256 a);

    function add(UFixed af, UFixed bf) external pure returns(UFixed abf);
    function sub(UFixed af, UFixed bf) external pure returns(UFixed abf);
    function delta(UFixed af, UFixed bf) external pure returns(UFixed abf);

    function mul(UFixed af, UFixed bf) external pure returns(UFixed abf);
    function div(UFixed af, UFixed bf) external pure returns(UFixed abf);

    function gt(UFixed af, UFixed bf) external pure returns(bool isGreaterThan);
    function eq(UFixed af, UFixed bf) external pure returns(bool isEqual);

    function gtz(UFixed af) external pure returns(bool isZero);
    function eqz(UFixed af) external pure returns(bool isZero);

    function multiplier() external pure returns(uint256 m);
}