"""Row573 hardening: exact-type subclass pins (int subclasses incl. IntEnum and
lying-comparison int subclasses at duration and machines slots; list/tuple
subclass and namedtuple containers at the durations slot), refusal-before-cap,
full-message pins, an independent subset-partition oracle, non-adjacent-order
and mixed-validity witnesses, boundary accepts, structural invariants, and a
mutation sweep. Tests-only delta: the module already uses exact type() checks.

Equivalent mutants documented (verified by reasoning, not chased):
  - 'while sub:' -> 'while sub > 1:': skipping sub==1 (the task-0 singleton)
    never changes the DP result, because every partition is also found with
    task 0 on the un-picked remainder side - the final two-way split always
    sees both complements, and earlier rounds can pick any other part first.
  - 'nxt = best[:]' -> 'nxt = total[:]': the init is only an upper bound;
    the sub-enumeration includes sub==mask (v == total[mask]), so the minimum
    over candidates is identical either way.
From the extended ad-hoc sweep:
  - memo key 'tuple(loads[:used])' -> 'tuple(loads)': machines >= used always
    carry load 0 at dfs entry, so both key forms carry identical information.
  - 'if key in dead:' -> 'if False:' (memoization disabled): correctness is
    unchanged; under the 10-task/5-machine caps the un-memoized DFS still
    finishes in ~0.05 s on the battery's largest cases (verified directly),
    so this is a performance-only mutant the caps keep untestable here.
  - 'min(used + 1, m)' -> 'min(used + 2, m)': unreachable in the returned
    assignment - dfs tries k in increasing order and returns the first
    success, and valid completions of the gapped branch relabel (swap the two
    machine numbers) onto valid completions of the k==used branch, which is
    always tried first, so the gap branch is only reached when it can add
    nothing.
"""
import pathlib
import random
import signal
import types
from collections import namedtuple
from enum import IntEnum

import pytest

from sugarcode.extra_doc import resource_schedule as mod

SRC = pathlib.Path(mod.__file__).read_text()
T_, V_ = TypeError, ValueError


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


def _survives(battery, old, new):
    doc_end = SRC.index('"""', 3) + 3
    assert SRC.find(old) > doc_end, 'mutation target must be code, not the docstring'
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    code = compile(mutated, 'mutant', 'exec')  # a syntax error is not a kill
    def _timeout(*_):
        raise TimeoutError('mutant did not terminate')
    previous = signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    return True


class L(list):
    pass


class T(tuple):
    pass


class PlainInt(int):
    pass


class LyingCmpInt(int):
    def __ge__(self, other):
        return True

    def __le__(self, other):
        return True


class AsymInt(int):
    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True


class Mach(IntEnum):
    one = 1
    six = 6


NT = namedtuple('NT', 'a b c')


def _subsets(mask):
    s = mask
    while True:
        yield s
        if s == 0:
            return
        s = (s - 1) & mask


def _oracle(ds, m):
    """Independent oracle: enumerate machine-by-machine subset partitions and
    take (makespan, assignment) minimal with lexicographic assignment tie-break."""
    n = len(ds)
    full = (1 << n) - 1
    best = None  # (makespan, assignment tuple, loads tuple)

    def rec(k, remaining, assign, loads):
        nonlocal best
        if k == m:
            if remaining:
                return
            mk = max(loads)
            cand = (mk, tuple(assign), tuple(loads))
            if best is None or (mk, tuple(assign)) < (best[0], best[1]):
                best = cand
            return
        for sub in _subsets(remaining):
            if sub == 0 and remaining:
                continue  # an empty machine before all tasks are placed breaks first-use order
            if sum(ds[i] for i in range(n) if sub >> i & 1) > (best[0] if best else 10**9):
                continue
            a2 = assign[:]
            for i in range(n):
                if sub >> i & 1:
                    a2[i] = k
            rec(k + 1, remaining ^ sub, a2, loads + [sum(ds[i] for i in range(n) if sub >> i & 1)])
            if not remaining:
                break  # trailing machines must stay empty; empty choice already tried via sub==0... handled below
    # machine 0..: choose subsets; when remaining becomes 0 the rest are empty
    def rec2(k, remaining, assign, loads):
        nonlocal best
        if remaining == 0:
            mk = max(loads) if loads else 0
            full_loads = loads + [0] * (m - len(loads))
            cand = (mk, tuple(assign), tuple(full_loads))
            if best is None or (mk, tuple(assign)) < (best[0], best[1]):
                best = cand
            return
        if k == m:
            return
        for sub in _subsets(remaining):
            if sub == 0:
                continue
            load = sum(ds[i] for i in range(n) if sub >> i & 1)
            if best is not None and load > best[0] and max(loads + [load]) >= best[0]:
                if load > best[0]:
                    continue
            a2 = assign[:]
            for i in range(n):
                if sub >> i & 1:
                    a2[i] = k
            rec2(k + 1, remaining ^ sub, a2, loads + [load])

    rec2(0, full, [None] * n, [])
    return {'makespan': best[0], 'assignment': list(best[1]), 'loads': list(best[2])}


def _check_shape(r, ds, m):
    assert set(r) == {'makespan', 'assignment', 'loads'}
    assert len(r['assignment']) == len(ds) and len(r['loads']) == m
    assert all(type(x) is int for x in r['assignment'] + r['loads'] + [r['makespan']])
    assert sum(r['loads']) == sum(ds) and max(r['loads']) == r['makespan']
    seen = -1
    for x in r['assignment']:
        assert 0 <= x < m and x <= seen + 1
        seen = max(seen, x)
    loads = [0] * m
    for d, x in zip(ds, r['assignment']):
        loads[x] += d
    assert loads == r['loads']
    assert r['makespan'] >= max(ds) and r['makespan'] >= -(-sum(ds) // m)


def _core(m):
    at = m.assign_tasks
    assert at([3, 3, 2, 2, 2], 2) == {'makespan': 6, 'assignment': [0, 0, 1, 1, 1], 'loads': [6, 6]}
    assert at([5], 3) == {'makespan': 5, 'assignment': [0], 'loads': [5, 0, 0]}
    assert at([4, 3, 3, 2, 2, 1], 3) == {'makespan': 5, 'assignment': [0, 1, 2, 1, 2, 0], 'loads': [5, 5, 5]}
    assert at([7, 7, 7], 1) == {'makespan': 21, 'assignment': [0, 0, 0], 'loads': [21]}
    assert at([4, 4, 4], 3) == {'makespan': 4, 'assignment': [0, 1, 2], 'loads': [4, 4, 4]}
    assert at([9, 1], 5) == {'makespan': 9, 'assignment': [0, 1], 'loads': [9, 1, 0, 0, 0]}
    assert at([5, 5, 4, 4, 3, 3, 3, 3], 3)['makespan'] == 10
    assert at([1000] * 10, 3) == {'makespan': 4000, 'assignment': [0] * 4 + [1] * 4 + [2] * 2,
                                  'loads': [4000, 4000, 2000]}
    assert at([1] * 10, 5) == {'makespan': 2, 'assignment': [0, 0, 1, 1, 2, 2, 3, 3, 4, 4],
                               'loads': [2, 2, 2, 2, 2]}
    # tuple container accepted
    assert at((3, 1, 2), 2) == at([3, 1, 2], 2)
    # seeded random cases against the independent subset-partition oracle
    rng = random.Random(5731)
    for _ in range(80):
        n = rng.randint(1, 6)
        mm = rng.randint(1, 3)
        ds = [rng.randint(1, 9) for _ in range(n)]
        assert at(ds, mm) == _oracle(ds, mm)
    # structural invariants at cap sizes (too big for the subset oracle)
    for ds, mm in ([1000, 999, 998, 997, 996, 995, 994, 993, 992, 991], 5), ([1000] * 10, 5), ([1] * 10, 1):
        _check_shape(at(ds, mm), ds, mm)
    assert at([1000, 999, 998, 997, 996, 995, 994, 993, 992, 991], 5)['makespan'] == 1991
    # full exact error messages
    _raises(T_, 'durations must be a list or tuple', at, 'ab', 1)
    _raises(T_, 'durations must be a list or tuple', at, {1}, 1)
    _raises(V_, 'task count must be between 1 and 10', at, [], 1)
    _raises(V_, 'task count must be between 1 and 10', at, [1] * 11, 1)
    _raises(T_, 'duration must be a nonbool int', at, [1, True], 1)
    _raises(T_, 'duration must be a nonbool int', at, [1.0], 1)
    _raises(T_, 'duration must be a nonbool int', at, ['1'], 1)
    _raises(T_, 'machines must be a nonbool int', at, [1], True)
    _raises(T_, 'machines must be a nonbool int', at, [1], 2.0)
    _raises(V_, 'duration must be between 1 and 1000', at, [0], 1)
    _raises(V_, 'duration must be between 1 and 1000', at, [1, -5], 1)
    _raises(V_, 'duration must be between 1 and 1000', at, [1001], 1)
    _raises(V_, 'machines must be between 1 and 5', at, [1], 0)
    _raises(V_, 'machines must be between 1 and 5', at, [1], 6)
    _raises(V_, 'machines must be between 1 and 5', at, [1], -1)
    # boundary accepts
    at([1] * 10, 1)
    at([1000], 5)
    at([1], 5)
    assert at([1000], 1)['makespan'] == 1000 and at([1], 1)['makespan'] == 1


def _mix(m):
    at = m.assign_tasks
    # non-adjacent bad entries and mixed validity after valid earlier entries
    _raises(T_, 'duration must be a nonbool int', at, [1, 2, 3, 'x'], 1)
    _raises(V_, 'duration must be between 1 and 1000', at, [1, 2, 3, 1001], 1)
    _raises(T_, 'duration must be a nonbool int', at, [1, 2, PlainInt(3)], 1)
    _raises(T_, 'duration must be a nonbool int', at, [1, 2, LyingCmpInt(1001)], 1)
    _raises(T_, 'duration must be a nonbool int', at, [1, 2, AsymInt(3)], 1)
    _raises(T_, 'machines must be a nonbool int', at, [1, 2], Mach.one)
    _raises(T_, 'machines must be a nonbool int', at, [1, 2], PlainInt(2))
    # ordering: durations fully validated before machines; first bad duration wins in order
    _raises(T_, 'duration must be a nonbool int', at, [True, 0], 99)
    _raises(V_, 'duration must be between 1 and 1000', at, [0, True], 99)
    _raises(V_, 'task count must be between 1 and 10', at, [], 'y')
    _raises(T_, 'duration must be a nonbool int', at, [1, 'x'], 'not-an-int')


def _late(m):
    at = m.assign_tasks
    # container subclasses refused, including namedtuple (a tuple subclass)
    _raises(T_, 'durations must be a list or tuple', at, L([1, 2]), 1)
    _raises(T_, 'durations must be a list or tuple', at, T((1, 2)), 1)
    _raises(T_, 'durations must be a list or tuple', at, NT(1, 2, 3), 1)
    # int subclasses refused at every int slot, incl. IntEnum and lying comparisons
    _raises(T_, 'duration must be a nonbool int', at, [PlainInt(1)], 1)
    _raises(T_, 'duration must be a nonbool int', at, [LyingCmpInt(0)], 1)
    _raises(T_, 'duration must be a nonbool int', at, [AsymInt(1)], 1)
    _raises(T_, 'machines must be a nonbool int', at, [1], LyingCmpInt(1))
    _raises(T_, 'machines must be a nonbool int', at, [1], AsymInt(1))
    # subclass refused before any cap/range check
    _raises(T_, 'durations must be a list or tuple', at, L([1] * 11), 1)
    _raises(T_, 'duration must be a nonbool int', at, [LyingCmpInt(1001)], 1)
    _raises(T_, 'duration must be a nonbool int', at, [LyingCmpInt(0)], 1)
    _raises(T_, 'machines must be a nonbool int', at, [1], Mach.six)
    _raises(T_, 'machines must be a nonbool int', at, [1], LyingCmpInt(6))
    # exact list-shaped and tuple-shaped acceptance counterparts
    assert at(list([3, 1, 2]), 2) == at((3, 1, 2), 2)


def battery(m):
    _core(m)
    _mix(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('type(v) is not int', 'not isinstance(v, int)'),
    ('type(durations) not in (list, tuple)', 'not isinstance(durations, (list, tuple))'),
    ('MAX_TASKS = 10', 'MAX_TASKS = 11'),
    ('MAX_MACHINES = 5', 'MAX_MACHINES = 6'),
    ('MAX_DURATION = 1000', 'MAX_DURATION = 1001'),
    ('if not 1 <= len(durations) <= MAX_TASKS', 'if not 1 <= len(durations) < MAX_TASKS'),
    ('if not 1 <= v <= MAX_DURATION', 'if not 1 < v <= MAX_DURATION'),
    ('if not 1 <= m <= MAX_MACHINES', 'if not 1 <= m < MAX_MACHINES'),
    ('low = mask & -mask', 'low = mask & (mask - 1)'),
    ('total[mask] = total[mask ^ low] + ds[low.bit_length() - 1]',
     'total[mask] = total[mask ^ low] + ds[low.bit_length()]'),
    ('for _ in range(m - 1)', 'for _ in range(m - 2)'),
    ('sub = (sub - 1) & mask', 'sub = (sub - 1) | mask'),
    ('if v < nxt[mask]', 'if v < nxt[mask] and False'),
    ('for k in range(min(used + 1, m))', 'for k in range(min(used, m))'),
    ('if loads[k] + ds[i] <= limit', 'if loads[k] + ds[i] < limit'),
    ('assign[i] = k', 'assign[i] = k + 1'),
    ('if dfs(i + 1, max(used, k + 1))', 'if dfs(i + 1, max(used, k))'),
    ("return {'makespan': limit, 'assignment': assign, 'loads': loads}",
     "return {'makespan': limit + 1, 'assignment': assign, 'loads': loads}"),
    ("'loads': loads}", "'loads': sorted(loads)}"),
    ("'assignment': assign,", "'assignment': list(reversed(assign)),"),
    ("'durations must be a list or tuple'", "'durations must be a list'"),
    ("'task count must be between 1 and 10'", "'task count must be between 1 and 9'"),
    ("' must be a nonbool int'", "' must be an int'"),
    ("'duration must be between 1 and 1000'", "'duration must be between 1 and 999'"),
    ("'machines must be between 1 and 5'", "'machines must be between 1 and 4'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
