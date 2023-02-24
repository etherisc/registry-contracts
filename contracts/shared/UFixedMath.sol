// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/utils/math/Math.sol";
import "./IUFixedMath.sol";

contract UFixedMath is
    IUFixedMath
{

    int8 public constant EXP = 18;
    uint256 public constant MULTIPLIER = 10 ** uint256(int256(EXP));
    uint256 public constant MULTIPLIER_HALF = MULTIPLIER / 2;
    
    Rounding public constant ROUNDING_DEFAULT = Rounding.HalfUp;

    function itof(uint256 a)
        public
        override
        pure
        returns(UFixed af)
    {
        return UFixed.wrap(a * MULTIPLIER);
    }

    function itof(uint256 a, int8 exp)
        public
        override
        pure
        returns(UFixed af)
    {
        require(EXP + exp >= 0, "ERROR:FM-010:EXPONENT_TOO_SMALL");
        require(EXP + exp <= 2 * EXP, "ERROR:FM-011:EXPONENT_TOO_LARGE");

        return UFixed.wrap(a * 10 ** uint8(EXP + exp));
    }

    function ftoi(UFixed af)
        public
        override
        pure
        returns(uint256 a)
    {
        return ftoi(af, ROUNDING_DEFAULT);
    }

    function ftoi(UFixed af, Rounding rounding)
        public
        override
        pure
        returns(uint256 a)
    {
        if(rounding == Rounding.HalfUp) {
            return Math.mulDiv(UFixed.unwrap(af) + MULTIPLIER_HALF, 1, MULTIPLIER, Math.Rounding.Down);
        } else if(rounding == Rounding.Down) {
            return Math.mulDiv(UFixed.unwrap(af), 1, MULTIPLIER, Math.Rounding.Down);
        } else {
            return Math.mulDiv(UFixed.unwrap(af), 1, MULTIPLIER, Math.Rounding.Up);
        }
    }

    function add(UFixed af, UFixed bf) 
        public
        override
        pure
        returns(UFixed abf)
    {
        return UFixed.wrap(
            UFixed.unwrap(af) + UFixed.unwrap(bf));
    }

    function sub(UFixed af, UFixed bf) 
        public
        override
        pure
        returns(UFixed abf)
    {
        return UFixed.wrap(
            UFixed.unwrap(af) - UFixed.unwrap(bf));
    }

    function delta(UFixed af, UFixed bf) 
        public
        override
        pure
        returns(UFixed abf)
    {
        if(gt(af, bf)) {
            return sub(af, bf);
        }

        return sub(bf, af);
    }

    function mul(UFixed af, UFixed bf) 
        public
        override
        pure
        returns(UFixed abf)
    {
        return UFixed.wrap(
            Math.mulDiv(
                UFixed.unwrap(af), 
                UFixed.unwrap(bf), 
                MULTIPLIER));
    }


    function div(UFixed af, UFixed bf) 
        public
        override
        pure
        returns(UFixed abf)
    {
        require(gtz(bf), "ERROR:FM-020:DIVISOR_ZERO");
        return UFixed.wrap(
            Math.mulDiv(
                UFixed.unwrap(af), 
                MULTIPLIER,
                UFixed.unwrap(bf)));
    }


    function gt(UFixed af, UFixed bf) public override pure returns(bool isGreaterThan) {
        return UFixed.unwrap(af) > UFixed.unwrap(bf);
    }

    function eq(UFixed af, UFixed bf) public override pure returns(bool isEqual) {
        return UFixed.unwrap(af) == UFixed.unwrap(bf);
    }

    function gtz(UFixed af) public override pure returns(bool isZero) {
        return UFixed.unwrap(af) > 0;
    }

    function eqz(UFixed af) public override pure returns(bool isZero) {
        return UFixed.unwrap(af) == 0;
    }

    function multiplier() public override pure returns(uint256 multiplier) {
        return MULTIPLIER;
    }
}
