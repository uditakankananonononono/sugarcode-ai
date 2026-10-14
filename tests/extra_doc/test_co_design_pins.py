"""Row 352 tests-only hardening: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import pytest

from sugarcode.extra_doc.co_design import consensus_design as cd


class L(list):
    pass


class T(tuple):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        cd(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'utilities and minimums must be lists or tuples'
NC = 'candidate count must be between 1 and 64'
SC = 'stakeholder count must be between 1 and 8'
UR = 'utility rows must match stakeholders'
UT = 'utilities must be nonbool integers between -1000 and 1000'
MN = 'minimums must be nonbool integers between -1000 and 1000'
NO = 'no design meets every stakeholder minimum'


def oracle(u, m):
    feas = [i for i, row in enumerate(u) if all(a >= b for a, b in zip(row, m))]
    if not feas:
        return None
    def key(i):
        s = [a - b for a, b in zip(u[i], m)]
        return (-min(s), -sum(s), i)
    best = min(feas, key=key)
    return best, feas


CASES = [
    ([[5, 5], [9, 1], [4, 8]], [1, 1]),
    ([[5, 5], [9, 1], [4, 8]], [2, 2]),
    ([[3, 3], [3, 3]], [0, 0]),
    ([[1, 9], [5, 5]], [0, 0]),
    ([[1, 9], [5, 5]], [1, 5]),
    ([[-5, -5], [-3, -9]], [-5, -9]),
    ([[0, 0, 0], [1, 0, 0], [0, 1, 0]], [0, 0, 0]),
    ([[1000]], [-1000]),
]


@pytest.mark.parametrize('u,m', CASES)
def test_oracle(u, m):
    best, feas = oracle(u, m)
    r = cd(u, m)
    s = [a - b for a, b in zip(u[best], m)]
    assert r == {'candidate_index': best, 'stakeholder_surpluses': s, 'minimum_surplus': min(s), 'total_surplus': sum(s),
                 'feasible_indices': feas, 'collaboration_performed': False}


def test_literals_and_ties():
    assert cd([[5, 5], [9, 1], [4, 8]], [1, 1]) == {'candidate_index': 0, 'stakeholder_surpluses': [4, 4], 'minimum_surplus': 4,
                                                  'total_surplus': 8, 'feasible_indices': [0, 1, 2], 'collaboration_performed': False}
    assert cd([[3, 3], [3, 3]], [0, 0])['candidate_index'] == 0                              # full tie: first index
    assert cd([[2, 8], [4, 4]], [0, 0])['candidate_index'] == 1                              # max-min beats larger total
    assert cd([[4, 4], [4, 6]], [0, 0])['candidate_index'] == 1                              # same min: larger total
    assert cd([[3, 5]], [3, 5])['minimum_surplus'] == 0                                      # surplus 0 is allowed
    refuses(ValueError, NO, [[3, 5]], [3, 6])
    refuses(ValueError, NO, [[3, 5], [2, 9]], [3, 6])
    assert cd([[3, 5], [3, 6]], [3, 6])['candidate_index'] == 1


def test_caps_and_value_bounds():
    assert cd([[0]] * 64, [0])['feasible_indices'] == list(range(64))
    refuses(ValueError, NC, [[0]] * 65, [0])
    refuses(ValueError, NC, [], [0])
    assert cd([[0] * 8], [0] * 8)['total_surplus'] == 0
    refuses(ValueError, SC, [[0] * 9], [0] * 9)
    refuses(ValueError, SC, [[]], [])
    refuses(ValueError, UR, [[0, 0], [0]], [0, 0])
    refuses(ValueError, UR, [[0, 0], [0, 0, 0]], [0, 0])
    assert cd([[1000, -1000]], [-1000, -1000])['total_surplus'] == 2000
    for b in (-1001, 1001):
        refuses(ValueError, UT, [[b]], [0])
        refuses(ValueError, UT, [[0], [b]], [0])
        refuses(ValueError, MN, [[0]], [b])
        refuses(ValueError, MN, [[0, 0]], [0, b])


def test_exact_types():
    refuses(TypeError, TY, L([[0]]), [0])
    refuses(TypeError, TY, T(([0],)), [0])
    refuses(TypeError, TY, [[0]], L([0]))
    refuses(TypeError, TY, [[0]], T((0,)))
    for b in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, [0])
        refuses(TypeError, TY, [[0]], b)
    refuses(ValueError, UR, [L([0])], [0])
    refuses(ValueError, UR, [[0], T((0,))], [0])
    refuses(ValueError, UR, [[0], 'a'], [0])
    for b in (True, False, 1.0, I(1), '1', None):
        refuses(ValueError, UT, [[b]], [0])
        refuses(ValueError, UT, [[0], [b]], [0])
        refuses(ValueError, MN, [[0]], [b])
        refuses(ValueError, MN, [[0, 0]], [0, b])
    assert cd(((1,),), (0,)) == cd([[1]], [0])
    u = [[1]]
    r = cd(u, [0])
    r['stakeholder_surpluses'].append(9)
    assert u == [[1]]


def test_check_order():
    refuses(TypeError, TY, 1, 2)
    refuses(ValueError, NC, [], [])
    refuses(ValueError, SC, [[1]], [])
    refuses(ValueError, UR, [[True]], [0, 0])
    refuses(ValueError, UT, [[True]], [True])
    refuses(ValueError, MN, [[0]], [True])
    refuses(ValueError, NO, [[0]], [1])


def test_minimum_bounds_inclusive_at_both_ends():
    assert cd([[1000]], [1000])['stakeholder_surpluses'] == [0]
    assert cd([[1000]], [-1000])['stakeholder_surpluses'] == [2000]
    assert cd([[-1000]], [-1000])['stakeholder_surpluses'] == [0]
    refuses(ValueError, NO, [[999]], [1000])
