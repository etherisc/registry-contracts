import pytest
import brownie

# enforce function isolation for tests below
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

MULTIPLIER_EXPECTED = 10 ** 18
BIG = 10 ** 32 - 1


def test_fixture(math):
    assert math.multiplier() == MULTIPLIER_EXPECTED;


def test_itof(math):
    check_itof(0, math)
    check_itof(1, math)
    check_itof(42, math)
    check_itof(10 ** 32 - 1, math)


def test_itof_exp(math):
    assert math.itof(0, -10) == 0
    assert math.itof(0, -1) == 0
    assert math.itof(0, 0) == 0
    assert math.itof(0, 1) == 0
    assert math.itof(0, 10) == 0

    assert math.itof(1, -10) == math.multiplier() / 10 ** 10
    assert math.itof(1, -2) == math.multiplier() / 10 ** 2
    assert math.itof(1, -1) == math.multiplier() / 10
    assert math.itof(1, 0) == math.multiplier()
    assert math.itof(1, 1) == math.multiplier() * 10
    assert math.itof(1, 2) == math.multiplier() * 10 ** 2
    assert math.itof(1, 10) == math.multiplier() * 10 ** 10


def test_ftoi(math):
    check_ftoi(math.itof(0), math)
    check_ftoi(math.itof(1), math)
    check_ftoi(math.itof(42), math)
    check_ftoi(math.itof(10 ** 32 - 1), math)


def test_eq(math):
    check_op(0, 0, 'eq', math)
    check_op(1, 1, 'eq', math)
    check_op(2, 2, 'eq', math)
    check_op(42, 42, 'eq', math)
    check_op(10 ** 32 - 1, 10 ** 32 - 1, 'eq', math)


def test_gt(math):
    check_op(1, 0, 'gt', math)
    check_op(2, 1, 'gt', math)
    check_op(42, 11, 'gt', math)
    check_op(10 ** 32 - 1, 10 ** 32 - 2, 'gt', math)


def test_xz(math):
    check_op(0, 0, 'eqz', math)
    check_op(0, BIG, 'eqz', math)

    check_op(1, BIG, 'gtz', math)
    check_op(2, BIG, 'gtz', math)
    check_op(42, BIG, 'gtz', math)
    check_op(BIG, BIG, 'gtz', math)


def test_add(math):
    check_addsub(0, 0, 0, math)
    check_addsub(1, 0, 1, math)
    check_addsub(0, 1, 1, math)
    check_addsub(BIG - 1, 1, BIG, math)


def test_sub(math):
    check_addsub(1, -1, 0, math)
    check_addsub(2, -1, 1, math)
    check_addsub(3, -2, 1, math)
    check_addsub(BIG, -1, BIG - 1, math)

    a = math.itof(1)
    b = math.itof(2)

    with brownie.reverts('ERROR:UFM-010:NEGATIVE_RESULT'):
        math.sub(a, b)


def test_mul(math):
    check_muldiv(0, 0, 0, 'mul', math)
    check_muldiv(1, 0, 0, 'mul', math)
    check_muldiv(0, 1, 0, 'mul', math)
    check_muldiv(1, 1, 1, 'mul', math)
    check_muldiv(1, 2, 2, 'mul', math)
    check_muldiv(2, 21, 42, 'mul', math)
    check_muldiv(BIG, 1, BIG, 'mul', math)


def test_div(math):
    check_muldiv(0, 1, 0, 'div', math)
    check_muldiv(0, 2, 0, 'div', math)
    check_muldiv(0, BIG, 0, 'div', math)

    check_muldiv(1, 1, 1, 'div', math)
    check_muldiv(2, 1, 2, 'div', math)
    check_muldiv(BIG, 1, BIG, 'div', math)

    check_muldiv(2, 2, 1, 'div', math)
    check_muldiv(BIG, BIG, 1, 'div', math)

    a = math.itof(1)
    b = math.itof(0)

    with brownie.reverts('ERROR:UFM-020:DIVISOR_ZERO'):
        math.div(a, b)


def test_mul_frac(math):
    # 1/2 * 1/3 == 1/6
    one_half = to_frac(1, 2, math)
    one_third = to_frac(1, 3, math)
    one_6th = to_frac(1, 6, math)

    x = math.mul(one_half, one_third)
    assert math.eq(x, one_6th) is True
    assert math.dlt(x, one_6th) == 0

    # 1/3 * 1/3 == 1/9
    x = math.mul(one_third, one_third)
    x_expected = to_frac(1, 9, math)
    assert math.dlt(x, x_expected) == 1

    # 3/4 * 4/5 == 3/5
    three_4th = to_frac(3, 4, math)
    four_5th = to_frac(4, 5, math)
    x = math.mul(three_4th, four_5th)
    x_expected = to_frac(3 * 4, 4 * 5, math)
    assert math.eq(x, x_expected) is True
    assert math.dlt(x, x_expected) == 0

    # 1.25% of 3.1415926536
    p = 0.0125
    pi = 3.1415926536

    pf = math.itof(p * 10 ** 4, -4)
    pif = math.itof(pi * 10 ** 10, -10)
    x = math.mul(pf, pif)
    x_expected = math.multiplier() * p * pi
    assert math.eq(x, x_expected) is True
    assert math.dlt(x, x_expected) == 0


def to_frac(a, b, math):
    fa = math.itof(a)
    fb = math.itof(b)
    return math.div(fa, fb)


def check_muldiv(a, b, expected, op, math):
    fa = math.itof(a)
    fb = math.itof(b)
    fe = math.itof(expected)

    if op == 'mul':
        fab = math.mul(fa, fb)
        assert math.eq(fab, fe)
    elif op == 'div':
        fab = math.div(fa, fb)
        assert math.eq(fab, fe)


def check_addsub(a, b, expected, math):
    fa = math.itof(a)
    fe = math.itof(expected)

    if b >= 0:
        fb = math.itof(b)
        fab = math.add(fa, fb)
        assert math.eq(fab, fe)
    else:
        fb = math.itof(-b)
        fab = math.sub(fa, fb)
        assert math.eq(fab, fe)



def check_op(a, b, op, math):
    af = math.itof(a)
    bf = math.itof(b)

    if op == 'eq':
        assert math.eq(af, bf)
    elif op == 'gt':
        assert math.gt(af, bf)
    elif op == 'gtz':
        assert math.gtzUFixed(af)
    elif op == 'eqz':
        assert math.eqzUFixed(af)


def check_itof(a, math):
    af = math.itof(a)
    assert a == math.ftoi(af)


def check_ftoi(fa, math):
    a = math.ftoi(fa)
    assert fa == math.itof(a)
