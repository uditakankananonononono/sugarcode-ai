"""Row 358 tests-only hardening: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import itertools

import pytest

from sugarcode.extra_doc.transition_design import transition_portfolio as tp


class L(list):
    pass


class T(tuple):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        tp(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'inputs must be lists or tuples'
AC = 'action count must be between 1 and 12'
SH = 'action shapes must agree'
BG = 'budget must be a nonbool integer zero through 1000000'
PL = 'prerequisites must be lists or tuples of at most 12'
VL = 'costs and benefits must be nonbool integers zero through 1000000'
PI = 'prerequisite indices must be nonbool valid nonself indices'


def oracle(c, b, pre, bud):
    n = len(c)
    best, feas = None, 0
    for r in range(n + 1):
        for ch in itertools.combinations(range(n), r):
            if any(j not in ch for i in ch for j in pre[i]):
                continue
            cost = sum(c[i] for i in ch)
            if cost > bud:
                continue
            feas += 1
            key = (-sum(b[i] for i in ch), cost, ch)
            if best is None or key < best:
                best = key
    done, order = set(), []
    while len(order) < n:
        i = min(k for k in range(n) if k not in done and all(j in done for j in pre[k]))
        done.add(i)
        order.append(i)
    return best, feas, [i for i in order if i in best[2]]


CASES = [
    ([2, 3, 4], [5, 6, 9], [[], [0], [1]], 9),
    ([2, 3, 4], [5, 6, 9], [[], [0], [1]], 8),
    ([2, 3, 4], [5, 6, 9], [[], [0], [1]], 1),
    ([1, 1, 1], [1, 1, 1], [[], [], []], 2),
    ([5, 1], [0, 9], [[1], []], 5),
    ([1, 1, 1, 1], [3, 1, 4, 1], [[2], [2], [], [0, 1]], 4),
    ([3, 3], [4, 4], [[1], []], 6),
    ([0, 0, 0], [0, 0, 0], [[2], [0], []], 0),
    ([2, 2, 2], [9, 1, 9], [[1], [], [1]], 4),
]


@pytest.mark.parametrize('c,b,pre,bud', CASES)
def test_oracle(c, b, pre, bud):
    (neg, cost, ch), feas, order = oracle(c, b, pre, bud)
    assert tp(c, b, pre, bud) == {'action_indices': list(ch), 'execution_order': order, 'cost': cost, 'benefit': -neg,
                                  'feasible_count': feas, 'systemic_change_validated': False}


def test_literals_ties_and_order():
    r = tp([2, 3, 4], [5, 6, 9], [[], [0], [1]], 9)
    assert r['action_indices'] == [0, 1, 2] and r['execution_order'] == [0, 1, 2] and r['benefit'] == 20
    r = tp([2, 2, 2], [9, 1, 9], [[1], [], [1]], 4)
    r = tp([1, 1], [5, 5], [[1], []], 2)
    assert r['execution_order'] == [1, 0]                      # prerequisite first even though index is higher
    assert tp([1, 1], [5, 5], [[], []], 1)['action_indices'] == [0]
    assert tp([1, 2], [5, 5], [[], []], 3)['action_indices'] == [0, 1]
    assert tp([2, 1], [5, 5], [[], []], 2)['action_indices'] == [1]
    assert tp([4, 0], [0, 0], [[], []], 9)['action_indices'] == []
    assert tp([3], [4], [[]], 3)['action_indices'] == [0] and tp([3], [4], [[]], 2)['action_indices'] == []


def test_caps_and_value_bounds():
    r = tp([1] * 12, [1] * 12, [[]] * 12, 12)
    assert r['feasible_count'] == 4096
    refuses(ValueError, AC, [1] * 13, [1] * 13, [[]] * 13, 1)
    refuses(ValueError, AC, [], [], [], 1)
    refuses(ValueError, SH, [1], [1, 1], [[]], 1)
    refuses(ValueError, SH, [1], [1], [[], []], 1)
    for b in (-1, 1000001):
        refuses(ValueError, BG, [1], [1], [[]], b)
        refuses(ValueError, VL, [b], [1], [[]], 1)
        refuses(ValueError, VL, [1, b], [1, 1], [[], []], 1)
        refuses(ValueError, VL, [1], [b], [[]], 1)
        refuses(ValueError, VL, [1, 1], [1, b], [[], []], 1)
    assert tp([1000000], [1000000], [[]], 1000000)['benefit'] == 1000000
    ok12 = [list(range(1, 12))] + [[]] * 11
    assert tp([1] * 12, [1] * 12, ok12, 12)['execution_order'][:1] == [1] and len(ok12[0]) == 11
    refuses(ValueError, PL, [1] * 12, [1] * 12, [list(range(13))] + [[]] * 11, 1)
    for b in (-1, 2):
        refuses(ValueError, PI, [1, 1], [1, 1], [[], [b]], 1)
    refuses(ValueError, PI, [1, 1], [1, 1], [[0], []], 1)
    refuses(ValueError, 'prerequisites must be unique', [1, 1], [1, 1], [[1, 1], []], 1)
    refuses(ValueError, 'prerequisites must be unique', [1, 1, 1], [1, 1, 1], [[], [], [0, 0]], 1)
    refuses(ValueError, 'prerequisite graph must be acyclic', [1, 1], [1, 1], [[1], [0]], 1)
    refuses(ValueError, 'prerequisite graph must be acyclic', [1, 1, 1], [1, 1, 1], [[], [2], [1]], 1)


def test_twelve_prerequisites_is_the_cap():
    refuses(ValueError, PL, [1] * 12, [1] * 12, [[1] * 13] + [[]] * 11, 1)
    assert tp([1] * 12, [1] * 12, [list(range(1, 12))] + [[]] * 11, 12)['cost'] == 12


def test_exact_types():
    refuses(TypeError, TY, L([1]), [1], [[]], 1)
    refuses(TypeError, TY, [1], L([1]), [[]], 1)
    refuses(TypeError, TY, [1], [1], L([[]]), 1)
    refuses(TypeError, TY, T((1,)), [1], [[]], 1)
    for b in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, [1], [[]], 1)
        refuses(TypeError, TY, [1], b, [[]], 1)
        refuses(TypeError, TY, [1], [1], b, 1)
    refuses(ValueError, PL, [1], [1], [L([])], 1)
    refuses(ValueError, PL, [1, 1], [1, 1], [[], T(())], 1)
    refuses(ValueError, PL, [1, 1], [1, 1], [[], 'a'], 1)
    for b in (True, False, 1.0, I(1), '1', None):
        refuses(ValueError, BG, [1], [1], [[]], b)
        refuses(ValueError, VL, [b], [1], [[]], 1)
        refuses(ValueError, VL, [1, b], [1, 1], [[], []], 1)
        refuses(ValueError, VL, [1], [b], [[]], 1)
        refuses(ValueError, VL, [1, 1], [1, b], [[], []], 1)
    refuses(ValueError, PI, [1, 1], [1, 1], [[], [True]], 1)
    refuses(ValueError, PI, [1, 1], [1, 1], [[], [I(0)]], 1)
    refuses(ValueError, PI, [1, 1], [1, 1], [[], [0.0]], 1)
    refuses(ValueError, PI, [1, 1], [1, 1], [[], ['0']], 1)
    refuses(ValueError, PI, [1, 1, 1], [1, 1, 1], [[], [0], [0, True]], 1)
    assert tp((1,), (1,), ((),), 1) == tp([1], [1], [[]], 1)


def test_check_order():
    refuses(TypeError, TY, 1, 2, 3, 4)
    refuses(ValueError, AC, [], [], [], True)
    refuses(ValueError, SH, [1], [], [], True)
    refuses(ValueError, BG, [True], [1], [[]], True)
    refuses(ValueError, PL, [True], [1], [5], 1)
    refuses(ValueError, VL, [True], [1], [[True]], 1)
    refuses(ValueError, PI, [1], [1], [[True]], 1)



def test_twelve_entry_prerequisite_list_passes_length_check_and_fails_later():
    refuses(ValueError, PI, [1] * 12, [1] * 12, [[]] * 11 + [list(range(12))], 1)
    refuses(ValueError, 'prerequisites must be unique', [1] * 12, [1] * 12, [[1] * 12] + [[]] * 11, 1)
    refuses(ValueError, PL, [1] * 12, [1] * 12, [[1] * 13] + [[]] * 11, 1)
