import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.game_learning import learn_zero_sum as lz


def test_hand_cases():
    r = lz([[1, 0], [0, 1]], 8)                         # matching-pennies style: uniform is already the equilibrium
    assert r['row_average'] == [F(1, 2)] * 2 and r['column_average'] == [F(1, 2)] * 2
    assert (r['value_lower'], r['value_upper'], r['exploitability'], r['is_equilibrium']) == (F(1, 2), F(1, 2), 0, True)
    # row 0 dominates: x = (1/2,1/2) then (1,0) forever; xbar0 = (1/2 + 7)/8 = 15/16
    r = lz([[1, 1], [0, 0]], 8)
    assert r['row_average'] == [F(15, 16), F(1, 16)]
    assert (r['value_lower'], r['value_upper'], r['exploitability'], r['is_equilibrium']) == (F(15, 16), 1, F(1, 16), False)
    r = lz([[F(1, 2)]], 3)
    assert r['row_average'] == [1] and r['exploitability'] == 0 and r['is_equilibrium'] is True


def _value_2x2(A):
    (a, b), (c, d) = A
    lo = max(min(a, b), min(c, d))
    hi = min(max(a, c), max(b, d))
    if lo == hi:
        return lo
    return (a * d - b * c) / (a + d - b - c)


def test_independent_oracle_bracket_and_recomputation():
    rnd = random.Random(2)
    for _ in range(200):
        m, n = rnd.randint(1, 4), rnd.randint(1, 4)
        A = [[F(rnd.randint(0, 6), 6) for _ in range(n)] for _ in range(m)]
        T = rnd.randint(1, 8)
        r = lz(A, T)
        xb, yb = r['row_average'], r['column_average']
        assert sum(xb) == 1 and sum(yb) == 1 and all(v >= 0 for v in xb + yb)
        upper = max(sum(A[i][j] * yb[j] for j in range(n)) for i in range(m))
        lower = min(sum(xb[i] * A[i][j] for i in range(m)) for j in range(n))
        assert (r['value_upper'], r['value_lower']) == (upper, lower)
        assert r['exploitability'] == upper - lower >= 0 and r['is_equilibrium'] == (upper == lower)
        if m == n == 2:
            v = _value_2x2(A)
            assert lower <= v <= upper


def test_independent_replay_of_the_dynamics():
    rnd = random.Random(4)
    for _ in range(60):
        m, n, T = rnd.randint(1, 3), rnd.randint(1, 3), rnd.randint(1, 6)
        A = [[F(rnd.randint(0, 5), 5) for _ in range(n)] for _ in range(m)]
        # replay with cumulative payoff sums instead of per-round regret updates
        x_hist, y_hist, u_hist, v_hist = [], [], [], []
        def pol(cum, earned, k):
            reg = [c - earned for c in cum]
            pos = [t if t > 0 else 0 for t in reg]
            return [F(1, k)] * k if sum(pos) == 0 else [t / sum(pos) for t in pos]
        cu, cv, eu, ev = [F(0)] * m, [F(0)] * n, F(0), F(0)
        for _ in range(T):
            x, y = pol(cu, eu, m), pol(cv, ev, n)
            u = [sum(A[i][j] * y[j] for j in range(n)) for i in range(m)]
            v = [-sum(x[i] * A[i][j] for i in range(m)) for j in range(n)]
            cu = [cu[i] + u[i] for i in range(m)]
            cv = [cv[j] + v[j] for j in range(n)]
            eu += sum(x[i] * u[i] for i in range(m))
            ev += sum(y[j] * v[j] for j in range(n))
            x_hist.append(x)
            y_hist.append(y)
        r = lz(A, T)
        assert r['row_average'] == [sum(x[i] for x in x_hist) / T for i in range(m)]
        assert r['column_average'] == [sum(y[j] for y in y_hist) / T for j in range(n)]


def test_boundaries_and_caps():
    big = 2 ** 32 - 1
    assert lz([[F(1, big)]], 1)
    assert lz([[0] * 4] * 4, 8) and lz([[1]], 1)
    for bad in (2 ** 32, F(1, 2 ** 32), F(2 ** 32, 3)):
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            lz([[bad]], 1)


@pytest.mark.parametrize('args,err,msg', [
    (([[1]], True), TypeError, 'rounds must be a nonbool int'),
    (([[1]], 0), ValueError, 'rounds must be between 1 and 8'),
    (([[1]], 9), ValueError, 'rounds must be between 1 and 8'),
    (('x', 1), ValueError, 'A must have 1 to 4 rows'),
    (([], 1), ValueError, 'A must have 1 to 4 rows'),
    (([[1]] * 5, 1), ValueError, 'A must have 1 to 4 rows'),
    (([1], 1), TypeError, 'A must be a list or tuple of rows'),
    (([[]], 1), ValueError, 'A must have 1 to 4 columns'),
    (([[1] * 5, [1]], 1), ValueError, 'A must have 1 to 4 columns'),
    (([[1, 1], [1]], 1), ValueError, 'A rows must have equal length'),
    (([[True]], 1), TypeError, 'values must be nonbool int or Fraction'),
    (([[-1]], 1), ValueError, r'entries must be in \[0, 1\]'),
    (([[2]], 1), ValueError, r'entries must be in \[0, 1\]'),
])
def test_exact_errors(args, err, msg):
    with pytest.raises(err, match='^' + msg + '$'):
        lz(*args)


def test_mixed_valid_and_invalid_entries_every_position():
    for pos in range(4):
        flat = [F(1, 2)] * 4
        flat[pos] = F(-1, 2) if pos % 2 else F(3, 2)
        with pytest.raises(ValueError, match=r'^entries must be in \[0, 1\]$'):
            lz([flat[:2], flat[2:]], 1)


def test_numerator_32_bit_boundary():
    big = 2 ** 32 - 1
    assert lz([[F(big - 1, big)]], 1)
    with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
        lz([[F(2 ** 32, 2 ** 32 + 1)]], 1)
