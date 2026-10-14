"""Row 360 tests-only hardening: exact oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc.market_size_estimation import market_funnel as mf


class L(list):
    pass


class T(tuple):
    pass


class I(int):
    pass


class Fr(F):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        mf(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'segments must be a list or tuple'
SH = 'segments must contain count annual_spend serviceable obtainable'
CT = 'customer counts must be nonbool integers zero through 4294967295'
NUM = 'values must be nonbool int or Fraction'
BITS = 'values must fit 32 bits'
FR = 'fractions must be between zero and one'
SP = 'annual spend must be nonnegative'
OK = [(10, 5, 1, 1)]


def test_exact_oracle_and_literals():
    segs = [(100, 20, F(1, 2), F(1, 4)), (3, F(7, 3), 1, F(2, 3)), (0, 5, 1, 1), (7, 0, 0, 0)]
    r = mf(segs)
    rows = []
    for c, p, s, o in segs:
        tam = F(c) * F(p)
        rows.append({'tam': tam, 'sam': tam * F(s), 'som': tam * F(s) * F(o)})
    assert r == {'segments': rows, 'totals': {k: sum(x[k] for x in rows) for k in ('tam', 'sam', 'som')},
                 'forecast_validated': False}
    assert rows[0] == {'tam': 2000, 'sam': 1000, 'som': 250}
    assert r['totals'] == {'tam': 2007, 'sam': 1007, 'som': 250 + F(14, 3)}
    assert all(type(v) is F for row in r['segments'] for v in row.values())
    assert all(type(v) is F for v in r['totals'].values())
    assert mf(((1, 1, 1, 1),)) == mf([[1, 1, 1, 1]])
    assert mf([(2, 3, 0, 1)])['segments'][0] == {'tam': 6, 'sam': 0, 'som': 0}


def test_caps_and_bounds_n_and_n_plus_1():
    assert mf([(1, 1, 1, 1)] * 64)['totals']['tam'] == 64
    refuses(ValueError, 'segment count must be between 1 and 64', [(1, 1, 1, 1)] * 65)
    refuses(ValueError, 'segment count must be between 1 and 64', [])
    assert mf([(2 ** 32 - 1, 1, 1, 1)])['totals']['tam'] == 2 ** 32 - 1
    assert mf([(0, 1, 1, 1)])['totals']['tam'] == 0
    for b in (-1, 2 ** 32):
        refuses(ValueError, CT, [(b, 1, 1, 1)])
        refuses(ValueError, CT, OK + [(b, 1, 1, 1)])
    assert mf([(1, 2 ** 32 - 1, 1, 1)])['totals']['tam'] == 2 ** 32 - 1
    assert mf([(1, F(2 ** 32 - 1, 7), 1, 1)])['totals']['tam'] == F(2 ** 32 - 1, 7)
    assert mf([(1, F(1, 2 ** 32 - 1), 1, 1)])['totals']['tam'] == F(1, 2 ** 32 - 1)
    for bad in (2 ** 32, -(2 ** 32), F(2 ** 32, 3), F(1, 2 ** 32)):
        refuses(ValueError, BITS, [(1, bad, 1, 1)])
        refuses(ValueError, BITS, OK + [(1, bad, 1, 1)])
        refuses(ValueError, BITS, [(1, 1, bad, 1)])
        refuses(ValueError, BITS, [(1, 1, 1, bad)])
        refuses(ValueError, BITS, OK + [(1, 1, 1, bad)])
    refuses(ValueError, SP, [(1, -1, 1, 1)])
    refuses(ValueError, SP, OK + [(1, F(-1, 2), 1, 1)])
    for bad in (-1, 2, F(-1, 3), F(3, 2)):
        refuses(ValueError, FR, [(1, 1, bad, 1)])
        refuses(ValueError, FR, [(1, 1, 1, bad)])
        refuses(ValueError, FR, OK + [(1, 1, bad, 1)])
        refuses(ValueError, FR, OK + [(1, 1, 1, bad)])
    assert mf([(1, 1, 0, 0)])['totals'] == {'tam': 1, 'sam': 0, 'som': 0}
    assert mf([(1, 1, 1, 1)])['totals'] == {'tam': 1, 'sam': 1, 'som': 1}
    assert mf([(1, 1, F(1, 2), F(1, 3))])['segments'][0]['som'] == F(1, 6)


def test_exact_types():
    refuses(TypeError, TY, L(OK))
    refuses(TypeError, TY, T(tuple(OK)))
    for b in (None, 'abcd', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b)
    refuses(ValueError, SH, [L([1, 1, 1, 1])])
    refuses(ValueError, SH, OK + [T((1, 1, 1, 1))])
    refuses(ValueError, SH, OK + [(1, 1, 1)])
    refuses(ValueError, SH, OK + [(1, 1, 1, 1, 1)])
    refuses(ValueError, SH, OK + ['abcd'])
    for b in (True, False, 1.0, I(1), '1', None, F(1)):
        refuses(ValueError, CT, [(b, 1, 1, 1)])
        refuses(ValueError, CT, OK + [(b, 1, 1, 1)])
    for b in (True, False, 1.0, I(1), Fr(1, 2), '1', None):
        refuses(TypeError, NUM, [(1, b, 1, 1)])
        refuses(TypeError, NUM, [(1, 1, b, 1)])
        refuses(TypeError, NUM, [(1, 1, 1, b)])
        refuses(TypeError, NUM, OK + [(1, b, 1, 1)])
        refuses(TypeError, NUM, OK + [(1, 1, 1, b)])
    s = [[1, 1, 1, 1]]
    r = mf(s)
    r['segments'].append(1)
    assert s == [[1, 1, 1, 1]]


def test_check_order():
    refuses(TypeError, TY, 1)
    refuses(ValueError, 'segment count must be between 1 and 64', [])
    refuses(ValueError, SH, [5])
    refuses(ValueError, CT, [(-1, 'x', 'y', 'z')])
    refuses(ValueError, CT, [(1, 'x', 'y', 'z'), (True, 1, 1, 1)])     # counts of every segment checked before any number
    refuses(TypeError, NUM, [(1, 'x', 'y', 'z')])
    refuses(TypeError, NUM, [(1, 1, 'y', 'z')])
    refuses(TypeError, NUM, [(1, -1, 'y', 'z')])                        # type before sign for spend
    refuses(ValueError, SP, [(1, -1, 2, 1)])                            # spend sign before fraction range
    refuses(ValueError, BITS, [(1, 2 ** 32, 2, 1)])
    refuses(ValueError, FR, [(1, 1, 2, 1)])
