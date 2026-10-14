"""Row 359 tests-only hardening: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import pytest

from sugarcode.extra_doc.service_design import service_schedule as ss


class L(list):
    pass


class T(tuple):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        ss(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'inputs must be lists or tuples'
SC = 'step count must be between 1 and 32'
SH = 'step shapes must agree'
PL = 'prerequisites must be lists or tuples of at most 32'
DU = 'durations must be nonbool integers between 1 and 1000000'
RS = 'resources must be nonbool integers zero through seven'
PI = 'prerequisites must be nonbool valid nonself indices'


def oracle(d, r, pre):
    n = len(d)
    end, start, free, rows, done = {}, {}, {}, [], []
    while len(done) < n:
        i = min(k for k in range(n) if k not in end and all(j in end for j in pre[k]))
        dep = max([end[j] for j in pre[i]] or [0])
        s = max(dep, free.get(r[i], 0))
        end[i] = s + d[i]
        free[r[i]] = end[i]
        rows.append({'step_index': i, 'resource': r[i], 'start': s, 'end': end[i], 'resource_wait': s - dep})
        done.append(i)
    return rows, max(end.values())


CASES = [
    ([3, 2, 4], [0, 0, 1], [[], [0], [0]]),
    ([3, 2, 4], [0, 0, 0], [[], [], []]),
    ([1, 1, 1], [0, 1, 2], [[], [0], [0, 1]]),
    ([5, 1], [7, 7], [[1], []]),
    ([2, 2, 2, 2], [0, 1, 0, 1], [[], [], [0], [1, 2]]),
    ([4], [3], [[]]),
    ([1, 9, 1], [2, 2, 2], [[], [], [0, 1]]),
]


@pytest.mark.parametrize('d,r,pre', CASES)
def test_oracle(d, r, pre):
    rows, span = oracle(d, r, pre)
    assert ss(d, r, pre) == {'steps': rows, 'makespan': span, 'service_execution_performed': False}


def test_literals():
    r = ss([3, 2, 4], [0, 0, 1], [[], [0], [0]])
    assert r['steps'] == [{'step_index': 0, 'resource': 0, 'start': 0, 'end': 3, 'resource_wait': 0},
                          {'step_index': 1, 'resource': 0, 'start': 3, 'end': 5, 'resource_wait': 0},
                          {'step_index': 2, 'resource': 1, 'start': 3, 'end': 7, 'resource_wait': 0}] and r['makespan'] == 7
    r = ss([3, 2], [0, 0], [[], []])
    assert r['steps'][1] == {'step_index': 1, 'resource': 0, 'start': 3, 'end': 5, 'resource_wait': 3}
    r = ss([1, 1], [0, 0], [[1], []])
    assert [s['step_index'] for s in r['steps']] == [1, 0]                       # prerequisite scheduled first
    assert ss([1000000], [7], [[]])['makespan'] == 1000000
    assert ss([1], [0], [[]])['makespan'] == 1
    assert ss([1] * 32, [0] * 32, [[]] * 32)['makespan'] == 32
    assert ss([1] * 8, list(range(8)), [[]] * 8)['makespan'] == 1


def test_caps_and_value_bounds():
    refuses(ValueError, SC, [1] * 33, [0] * 33, [[]] * 33)
    refuses(ValueError, SC, [], [], [])
    refuses(ValueError, SH, [1], [0, 0], [[]])
    refuses(ValueError, SH, [1], [0], [[], []])
    for b in (0, 1000001, -1):
        refuses(ValueError, DU, [b], [0], [[]])
        refuses(ValueError, DU, [1, b], [0, 0], [[], []])
    for b in (-1, 8):
        refuses(ValueError, RS, [1], [b], [[]])
        refuses(ValueError, RS, [1, 1], [0, b], [[], []])
    for b in (-1, 2):
        refuses(ValueError, PI, [1, 1], [0, 0], [[], [b]])
    refuses(ValueError, PI, [1, 1], [0, 0], [[0], [1]])
    refuses(ValueError, 'prerequisites must be unique', [1, 1], [0, 0], [[], [0, 0]])
    refuses(ValueError, 'prerequisite graph must be acyclic', [1, 1], [0, 0], [[1], [0]])
    refuses(ValueError, 'prerequisite graph must be acyclic', [1, 1, 1], [0, 0, 0], [[], [2], [1]])
    # 32-entry prerequisite list passes the length check and fails later; 33 fails the length check
    refuses(ValueError, PI, [1] * 32, [0] * 32, [[]] * 31 + [list(range(32))])
    refuses(ValueError, 'prerequisites must be unique', [1] * 32, [0] * 32, [[1] * 32] + [[]] * 31)
    refuses(ValueError, PL, [1] * 32, [0] * 32, [[1] * 33] + [[]] * 31)
    assert ss([1] * 32, [0] * 32, [[]] * 31 + [list(range(31))])['makespan'] == 32


def test_exact_types():
    refuses(TypeError, TY, L([1]), [0], [[]])
    refuses(TypeError, TY, [1], L([0]), [[]])
    refuses(TypeError, TY, [1], [0], L([[]]))
    refuses(TypeError, TY, T((1,)), [0], [[]])
    for b in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, [0], [[]])
        refuses(TypeError, TY, [1], b, [[]])
        refuses(TypeError, TY, [1], [0], b)
    refuses(ValueError, PL, [1], [0], [L([])])
    refuses(ValueError, PL, [1, 1], [0, 0], [[], T(())])
    refuses(ValueError, PL, [1, 1], [0, 0], [[], 'a'])
    for b in (True, False, 1.0, I(1), '1', None):
        refuses(ValueError, DU, [b], [0], [[]])
        refuses(ValueError, DU, [1, b], [0, 0], [[], []])
        refuses(ValueError, RS, [1, 1], [0, b], [[], []])
    refuses(ValueError, RS, [1], [False], [[]])
    refuses(ValueError, PI, [1, 1], [0, 0], [[], [True]])
    refuses(ValueError, PI, [1, 1], [0, 0], [[], [I(0)]])
    refuses(ValueError, PI, [1, 1], [0, 0], [[], [0.0]])
    refuses(ValueError, PI, [1, 1], [0, 0], [[], ['0']])
    refuses(ValueError, PI, [1, 1, 1], [0, 0, 0], [[], [0], [0, True]])
    assert ss((1,), (0,), ((),)) == ss([1], [0], [[]])


def test_check_order():
    refuses(TypeError, TY, 1, 2, 3)
    refuses(ValueError, SC, [], [], [])
    refuses(ValueError, SH, [True], [], [])
    refuses(ValueError, PL, [True], [True], [5])
    refuses(ValueError, DU, [True], [True], [[True]])
    refuses(ValueError, RS, [1], [True], [[True]])
    refuses(ValueError, PI, [1], [0], [[True]])
