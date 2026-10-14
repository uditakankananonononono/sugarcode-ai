"""Row574 hardening: exact-type subclass pins (plain/lying-comparison/
asymmetric-equality int subclasses and IntEnum at weight, value and capacity
slots; list/tuple subclasses and namedtuple pairs at the items and pair
slots), refusal-before-cap, full-message pins, an independent
include/exclude-recursion oracle, non-adjacent-order and mixed-validity
witnesses, boundary accepts, structural invariants at cap sizes, and a
mutation sweep. Tests-only delta: the module already uses exact type() checks.

Equivalent mutants documented from the extended sweep (not chased):
  - 'if take >= best' -> 'if take > best': the two branches differ only when
    take == best, and then the stored tuple is identical either way, so the
    table - and every downstream decision - is unchanged.
  - reconstruction '== table[i][c]' -> '>=': table[i][c] is the maximum of
    {skip, take}, so take can never be strictly greater; >= holds exactly
    when == holds.
"""
import pathlib
import random
import signal
import types
from collections import namedtuple
from enum import IntEnum

import pytest

from sugarcode.extra_doc import knapsack_best as mod

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


class Cap(IntEnum):
    ten = 10
    huge = 10001


Pair = namedtuple('Pair', 'weight value')


def _oracle(items, cap):
    """Independent oracle: recursive include/exclude over positions; among
    (value, weight) optima take the lexicographically smallest position list."""
    best = None  # (value, -weight, positions tuple)

    def rec(i, w, v, pos):
        nonlocal best
        if w > cap:
            return
        if i == len(items):
            key = (v, -w)
            if best is None or key > best[:2] or (key == best[:2] and pos < best[2]):
                best = (v, -w, pos)
            return
        rec(i + 1, w, v, pos)                       # leave item i
        rec(i + 1, w + items[i][0], v + items[i][1], pos + (i,))  # take item i

    rec(0, 0, 0, ())
    return {'value': best[0], 'weight': -best[1], 'chosen': list(best[2])}


def _check_shape(r, items, cap):
    assert set(r) == {'value', 'weight', 'chosen'}
    assert all(type(x) is int for x in [r['value'], r['weight']] + r['chosen'])
    assert r['chosen'] == sorted(r['chosen']) and len(set(r['chosen'])) == len(r['chosen'])
    assert all(0 <= i < len(items) for i in r['chosen'])
    assert sum(items[i][0] for i in r['chosen']) == r['weight'] <= cap
    assert sum(items[i][1] for i in r['chosen']) == r['value']
    assert r['weight'] >= 0 and r['value'] >= 0


def _core(m):
    bs = m.best_selection
    assert bs([(5, 10), (4, 40), (6, 30), (3, 50)], 10) == {'value': 90, 'weight': 7, 'chosen': [1, 3]}
    assert bs([], 0) == {'value': 0, 'weight': 0, 'chosen': []}
    assert bs([], 10000) == {'value': 0, 'weight': 0, 'chosen': []}
    assert bs([(1, 0)], 5) == {'value': 0, 'weight': 0, 'chosen': []}
    assert bs([(2, 3), (2, 3)], 2) == {'value': 3, 'weight': 2, 'chosen': [0]}
    assert bs([(2, 3), (2, 3)], 4) == {'value': 6, 'weight': 4, 'chosen': [0, 1]}
    assert bs([(5, 5)], 4) == {'value': 0, 'weight': 0, 'chosen': []}
    assert bs([(5, 5)], 5) == {'value': 5, 'weight': 5, 'chosen': [0]}
    assert bs([(4, 7), (3, 7)], 4) == {'value': 7, 'weight': 3, 'chosen': [1]}
    assert bs([(6, 30), (5, 16), (5, 16)], 10) == {'value': 32, 'weight': 10, 'chosen': [1, 2]}
    # a zero-value filler item is only taken when it is free in the tie break: weight must not grow
    assert bs([(2, 3), (1, 0)], 2) == {'value': 3, 'weight': 2, 'chosen': [0]}
    # tuple-shaped items container and mixed pair shapes accepted
    assert bs(((5, 10), [4, 40], (6, 30), [3, 50]), 10) == {'value': 90, 'weight': 7, 'chosen': [1, 3]}
    # seeded random cases against the independent include/exclude oracle
    rng = random.Random(5741)
    for _ in range(120):
        items = [(rng.randint(1, 6), rng.randint(0, 6)) for _ in range(rng.randint(0, 8))]
        cap = rng.randint(0, 20)
        assert bs(items, cap) == _oracle(items, cap)
    # structural invariants at cap sizes (beyond oracle reach)
    big1 = [(1000 - i, 999999 - i) for i in range(20)]
    _check_shape(bs(big1, 10000), big1, 10000)
    assert bs([(1000, 1000000)] * 10, 10000) == {'value': 10000000, 'weight': 10000, 'chosen': list(range(10))}
    assert bs([(1000, 1000000)] * 20, 10000)['chosen'] == list(range(10))
    # full exact error messages
    _raises(T_, 'items must be a list or tuple', bs, 'ab', 1)
    _raises(T_, 'items must be a list or tuple', bs, {(1, 1)}, 1)
    _raises(V_, 'item count must be between 0 and 20', bs, [(1, 1)] * 21, 1)
    _raises(T_, 'each item must be a (weight, value) pair', bs, [(1, 1), 5], 1)
    _raises(T_, 'each item must be a (weight, value) pair', bs, [(1, 1), (1,)], 1)
    _raises(T_, 'each item must be a (weight, value) pair', bs, [(1, 1), (1, 2, 3)], 1)
    _raises(T_, 'weight must be a nonbool int', bs, [(True, 1)], 1)
    _raises(T_, 'weight must be a nonbool int', bs, [(1.0, 1)], 1)
    _raises(T_, 'value must be a nonbool int', bs, [(1, '1')], 1)
    _raises(T_, 'value must be a nonbool int', bs, [(1, None)], 1)
    _raises(T_, 'capacity must be a nonbool int', bs, [(1, 1)], True)
    _raises(T_, 'capacity must be a nonbool int', bs, [(1, 1)], 2.0)
    _raises(V_, 'weight must be between 1 and 1000', bs, [(0, 1)], 1)
    _raises(V_, 'weight must be between 1 and 1000', bs, [(1001, 1)], 1)
    _raises(V_, 'value must be between 0 and 1000000', bs, [(1, -1)], 1)
    _raises(V_, 'value must be between 0 and 1000000', bs, [(1, 1000001)], 1)
    _raises(V_, 'capacity must be between 0 and 10000', bs, [(1, 1)], -1)
    _raises(V_, 'capacity must be between 0 and 10000', bs, [(1, 1)], 10001)
    # boundary accepts
    bs([(1, 1)] * 20, 0)
    bs([(1000, 0)], 10000)
    bs([(1, 1000000)], 0)
    assert bs([(1000, 1000000)], 1000)['value'] == 1000000


def _mix(m):
    bs = m.best_selection
    # non-adjacent bad entries and mixed validity after valid earlier entries
    _raises(T_, 'each item must be a (weight, value) pair', bs, [(1, 1), (2, 2), (3, 3), 9], 5)
    _raises(T_, 'weight must be a nonbool int', bs, [(1, 1), (2, 2), ('3', 3)], 5)
    _raises(T_, 'value must be a nonbool int', bs, [(1, 1), (2, 2), (3, PlainInt(3))], 5)
    _raises(T_, 'weight must be a nonbool int', bs, [(1, 1), (LyingCmpInt(1001), 2)], 5)
    _raises(T_, 'value must be a nonbool int', bs, [(1, 1), (2, AsymInt(2))], 5)
    _raises(T_, 'capacity must be a nonbool int', bs, [(1, 1)], Cap.ten)
    _raises(T_, 'capacity must be a nonbool int', bs, [(1, 1)], PlainInt(10))
    # ordering: both pair types before ranges; weight range before value range; items before capacity
    _raises(T_, 'value must be a nonbool int', bs, [(0, 1.5)], 'y')
    _raises(V_, 'weight must be between 1 and 1000', bs, [(0, -1)], 'y')
    _raises(T_, 'each item must be a (weight, value) pair', bs, [5, (0, 0)], 'y')
    _raises(V_, 'item count must be between 0 and 20', bs, [(1, 1)] * 21, 'y')
    _raises(V_, 'capacity must be between 0 and 10000', bs, [(1, 1)], 10 ** 6)


def _late(m):
    bs = m.best_selection
    # container subclasses refused, incl. a namedtuple pair (a tuple subclass)
    _raises(T_, 'items must be a list or tuple', bs, L([(1, 1)]), 1)
    _raises(T_, 'items must be a list or tuple', bs, T(((1, 1),)), 1)
    _raises(T_, 'each item must be a (weight, value) pair', bs, [L([1, 1])], 1)
    _raises(T_, 'each item must be a (weight, value) pair', bs, [T((1, 1))], 1)
    _raises(T_, 'each item must be a (weight, value) pair', bs, [Pair(1, 1)], 1)
    # int subclasses refused at every int slot, incl. IntEnum and lying comparisons
    _raises(T_, 'weight must be a nonbool int', bs, [(PlainInt(1), 1)], 1)
    _raises(T_, 'weight must be a nonbool int', bs, [(AsymInt(1), 1)], 1)
    _raises(T_, 'value must be a nonbool int', bs, [(1, LyingCmpInt(0))], 1)
    _raises(T_, 'capacity must be a nonbool int', bs, [(1, 1)], LyingCmpInt(5))
    _raises(T_, 'capacity must be a nonbool int', bs, [(1, 1)], AsymInt(5))
    # subclass refused before any cap/range check
    _raises(T_, 'items must be a list or tuple', bs, L([(1, 1)] * 21), 1)
    _raises(T_, 'weight must be a nonbool int', bs, [(LyingCmpInt(0), 1)], 1)
    _raises(T_, 'weight must be a nonbool int', bs, [(LyingCmpInt(1001), 1)], 1)
    _raises(T_, 'value must be a nonbool int', bs, [(1, LyingCmpInt(1000001))], 1)
    _raises(T_, 'value must be a nonbool int', bs, [(1, LyingCmpInt(-1))], 1)
    _raises(T_, 'capacity must be a nonbool int', bs, [(1, 1)], Cap.huge)
    _raises(T_, 'capacity must be a nonbool int', bs, [(1, 1)], LyingCmpInt(-1))
    # exact list-shaped and tuple-shaped acceptance counterparts
    assert bs(list([list([5, 10]), list([4, 40])]), 10) == bs(tuple([tuple([5, 10]), tuple([4, 40])]), 10)


def battery(m):
    _core(m)
    _mix(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('type(v) is not int', 'not isinstance(v, int)'),
    ('type(items) not in (list, tuple)', 'not isinstance(items, (list, tuple))'),
    ('type(p) not in (list, tuple) or len(p) != 2', 'not isinstance(p, (list, tuple)) or len(p) != 2'),
    ('MAX_ITEMS = 20', 'MAX_ITEMS = 21'),
    ('MAX_WEIGHT = 1000', 'MAX_WEIGHT = 1001'),
    ('MAX_VALUE = 1000000', 'MAX_VALUE = 1000001'),
    ('MAX_CAP = 10000', 'MAX_CAP = 10001'),
    ('if not 0 <= len(items) <= MAX_ITEMS', 'if not 0 <= len(items) < MAX_ITEMS'),
    ('if not 1 <= w <= MAX_WEIGHT', 'if not 1 < w <= MAX_WEIGHT'),
    ('if not 0 <= v <= MAX_VALUE', 'if not 0 < v <= MAX_VALUE'),
    ('if not 0 <= cap <= MAX_CAP', 'if not 0 < cap <= MAX_CAP'),
    ('    for i in range(n - 1, -1, -1):', '    for i in range(n - 2, -1, -1):'),
    ('            if c >= w:', '            if c > w:'),
    ('                take = (bv + v, bw - w)', '                take = (bv + v, bw)'),
    ('                if take >= best:', '                if False:'),
    ('        for c in range(cap + 1):', '        for c in range(cap):'),
    ('            best = nxt[c]', '            best = (0, 0)'),
    ('        its.append((w, v))', '        its.append((v, w))'),
    ('    table = [[(0, 0)] * (cap + 1) for _ in range(n + 1)]',
     '    table = [[(0, 1)] * (cap + 1) for _ in range(n + 1)]'),
    ('            if (bv + v, bw - w) == table[i][c]:', '            if (bv + v, bw - w) != table[i][c]:'),
    ('                chosen.append(i)', '                chosen.append(i + 1)'),
    ('                c -= w', '                c -= v'),
    ("return {'value': value, 'weight': -minus_w, 'chosen': chosen}",
     "return {'value': value, 'weight': minus_w, 'chosen': chosen}"),
    ("return {'value': value,", "return {'value': value + 1,"),
    ("'items must be a list or tuple'", "'items must be a list'"),
    ("'item count must be between 0 and 20'", "'item count must be between 0 and 19'"),
    ("'each item must be a (weight, value) pair'", "'each item must be a pair'"),
    ("' must be a nonbool int'", "' must be an int'"),
    ("'weight must be between 1 and 1000'", "'weight must be between 1 and 999'"),
    ("'value must be between 0 and 1000000'", "'value must be between 0 and 999999'"),
    ("'capacity must be between 0 and 10000'", "'capacity must be between 0 and 9999'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
