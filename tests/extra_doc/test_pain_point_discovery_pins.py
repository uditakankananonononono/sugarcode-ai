"""Row 369 tests-only hardening: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import pytest

from sugarcode.extra_doc.pain_point_discovery import discover_pain as dp


class L(list):
    pass


class T(tuple):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        dp(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'needs must be a list or tuple'
CNT = 'need count must be between 1 and 64'
TRI = 'needs must contain severity frequency satisfaction triples'
RAT = 'ratings must be nonbool integers zero through 100'


CASES = [
    [(10, 10, 0), (5, 5, 50), (100, 100, 0)],
    [(10, 10, 100), (0, 50, 0), (50, 0, 0)],
    [(2, 3, 4), (2, 3, 4), (3, 2, 4)],
    [(100, 100, 99)],
    [(1, 1, 99), (1, 1, 100)],
]


@pytest.mark.parametrize('needs', CASES)
def test_oracle(needs):
    sc = [a * b * (100 - c) for a, b, c in needs]
    pos = [i for i in range(len(sc)) if sc[i] > 0]
    pos.sort(key=lambda i: (-sc[i], i))
    assert dp(needs) == {'priorities': sc, 'unmet_need_indices': pos,
                         'zero_priority_indices': [i for i in range(len(sc)) if sc[i] == 0], 'needs_validated': False}


def test_literals_and_ties():
    r = dp([(10, 10, 0), (5, 5, 50), (100, 100, 0)])
    assert r['priorities'] == [10000, 1250, 1000000] and r['unmet_need_indices'] == [2, 0, 1]
    assert dp([(2, 3, 4), (2, 3, 4)])['unmet_need_indices'] == [0, 1]              # equal priority: input order
    r = dp([(10, 10, 100), (0, 50, 0), (50, 0, 0), (1, 1, 99)])
    assert r['zero_priority_indices'] == [0, 1, 2] and r['unmet_need_indices'] == [3]
    assert dp([(100, 100, 0)])['priorities'] == [1000000]
    assert dp([(1, 1, 99)])['priorities'] == [1] and dp([(1, 1, 100)])['priorities'] == [0]
    assert dp(((1, 2, 3),)) == dp([[1, 2, 3]])


def test_caps_and_bounds_n_and_n_plus_1():
    assert dp([(1, 1, 0)] * 64)['unmet_need_indices'] == list(range(64))
    refuses(ValueError, CNT, [(1, 1, 0)] * 65)
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [(1, 1)])
    refuses(ValueError, TRI, [(1, 1, 0), (1, 1, 0, 0)])
    for b in (-1, 101):
        for pos in range(3):
            row = [1, 1, 1]
            row[pos] = b
            refuses(ValueError, RAT, [row])
            refuses(ValueError, RAT, [(1, 1, 1), row])
    assert dp([(0, 0, 0)])['zero_priority_indices'] == [0]
    assert dp([(100, 100, 100)])['zero_priority_indices'] == [0]


def test_exact_types():
    refuses(TypeError, TY, L([(1, 1, 1)]))
    refuses(TypeError, TY, T(((1, 1, 1),)))
    for b in (None, 'abc', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b)
    refuses(ValueError, TRI, [L([1, 1, 1])])
    refuses(ValueError, TRI, [(1, 1, 1), T((1, 1, 1))])
    refuses(ValueError, TRI, [(1, 1, 1), 'abc'])
    for b in (True, False, 1.0, I(1), '1', None):
        for pos in range(3):
            row = [1, 1, 1]
            row[pos] = b
            refuses(ValueError, RAT, [row])
            refuses(ValueError, RAT, [(1, 1, 1), row])
    n = [[1, 1, 1]]
    r = dp(n)
    r['priorities'].append(5)
    assert n == [[1, 1, 1]]


def test_check_order():
    refuses(TypeError, TY, 1)
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [5])
    refuses(ValueError, RAT, [(True, 1, 1)])
