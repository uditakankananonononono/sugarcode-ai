import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import editorial_calendar408 as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __ne__(self, o): return False
    def __eq__(self, o): return True
    __hash__ = int.__hash__


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')



def test_scope_and_constants():
    assert mod.SCOPE == 'PARTIAL: first-free-week slot assignment over supplied items, no real dates'
    assert mod.NOT_CLAIMED == ('audience timing', 'content readiness', 'real dates', 'holidays',
                               'production readiness')
    assert 'NOT_CLAIMED' in mod.__doc__ and not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ITEMS, mod.MAX_NAME, mod.MAX_WEEK, mod.MAX_PER_WEEK) == (60, 40, 52, 7)


def _oracle(items, per_week):
    """Independent: week-by-week list of slots, scanning all 52 weeks."""
    weeks = {w: [] for w in range(1, 53)}
    slots, un = [], []
    for name, earliest in items:
        for w in range(earliest, 53):
            if len(weeks[w]) < per_week:
                weeks[w].append(name)
                slots.append((w, name))
                break
        else:
            un.append(name)
    return {'slots': slots, 'unscheduled': un, 'last_week': max([w for w, _ in slots]) if slots else None}


def test_placement_rules():
    assert mod.schedule([], 3) == {'slots': [], 'unscheduled': [], 'last_week': None}
    assert mod.schedule([('a', 1), ('b', 1), ('c', 1)], 2) == {
        'slots': [(1, 'a'), (1, 'b'), (2, 'c')], 'unscheduled': [], 'last_week': 2}
    # an item never runs before its earliest week
    assert mod.schedule([('a', 5)], 1)['slots'] == [(5, 'a')]
    # a later item with an earlier week takes the earlier free slot (placement order kept)
    assert mod.schedule([('a', 3), ('b', 1)], 1)['slots'] == [(3, 'a'), (1, 'b')]
    # a full week pushes the next item on to the following week, skipping full weeks
    assert mod.schedule([('a', 2), ('b', 3), ('c', 2), ('d', 2)], 1)['slots'] == [(2, 'a'), (3, 'b'), (4, 'c'), (5, 'd')]
    assert mod.schedule([('a', 1)], 7)['last_week'] == 1
    assert [w for w, _ in mod.schedule([(str(i), 1) for i in range(15)], 7)['slots']] == [1] * 7 + [2] * 7 + [3]
    # the year ends at week 52
    r = mod.schedule([('a', 52), ('b', 52), ('c', 51)], 1)
    assert r == {'slots': [(52, 'a'), (51, 'c')], 'unscheduled': ['b'], 'last_week': 52}
    r = mod.schedule([('a', 52), ('b', 52)], 2)
    assert r['slots'] == [(52, 'a'), (52, 'b')] and r['unscheduled'] == []
    assert mod.schedule([('a', 1), ('b', 1)], 1)['slots'] == [(1, 'a'), (2, 'b')]
    # tuples and lists accepted
    assert mod.schedule((('a', 1),), 1)['slots'] == [(1, 'a')] and mod.schedule([['a', 1]], 1)['slots'] == [(1, 'a')]
    # full year: 52 weeks x 1 slot placed, the 53rd item is unscheduled
    r = mod.schedule([('n%d' % i, 1) for i in range(60)], 1)
    assert len(r['slots']) == 52 and r['unscheduled'] == ['n%d' % i for i in range(52, 60)] and r['last_week'] == 52


def test_randomized_against_oracle():
    rng = random.Random(408)
    for _ in range(500):
        items = [('i%d' % i, rng.choice([1, 2, 3, 50, 51, 52])) for i in range(rng.randint(0, 25))]
        pw = rng.randint(1, 4)
        assert mod.schedule(items, pw) == _oracle(items, pw)


def test_validation_messages_boundaries_and_order():
    PER = 'per_week must be a nonbool int from 1 to 7'
    TYP = 'items must be a list or tuple'
    SIZ = 'items must hold at most 60 rows'
    SHP = 'each item must be a (name, earliest) list or tuple'
    NAM = 'names must be str of 1 to 40 characters'
    EAR = 'earliest must be a nonbool int from 1 to 52'
    DUP = 'names must be distinct'
    for bad in (0, 8, -1, True, False, 1.0, '1', None, I(1), 10 ** 30):
        _raises(ValueError, PER, mod.schedule, [], bad)
    assert mod.schedule([('a', 1)], 1)['last_week'] == 1 and mod.schedule([('a', 1)], 7)['last_week'] == 1
    for bad in (None, 'ab', 5, {}, L([]), T([])):
        _raises(TypeError, TYP, mod.schedule, bad, 1)
    _raises(ValueError, SIZ, mod.schedule, [('n%d' % i, 1) for i in range(61)], 1)
    assert len(mod.schedule([('n%d' % i, 1) for i in range(60)], 7)['slots']) == 60
    for bad in (None, 5, 'ab', ('a',), ('a', 1, 1), (), L(['a', 1]), T(['a', 1]), {'a': 1}):
        _raises(ValueError, SHP, mod.schedule, [bad], 1)
    for bad in ('', 'x' * 41, None, 5, b'a', S('a'), ['a']):
        _raises(ValueError, NAM, mod.schedule, [(bad, 1)], 1)
    assert mod.schedule([('x' * 40, 1)], 1)['slots'] == [(1, 'x' * 40)]
    for bad in (0, 53, -1, True, False, 1.0, '1', None, I(1), 10 ** 30):
        _raises(ValueError, EAR, mod.schedule, [('a', bad)], 1)
    assert mod.schedule([('a', 52)], 1)['slots'] == [(52, 'a')]
    _raises(ValueError, DUP, mod.schedule, [('a', 1), ('a', 2)], 1)
    assert mod.schedule([('a', 1), ('A', 1)], 2)['slots'] == [(1, 'a'), (1, 'A')]
    assert mod.schedule([('A', 1), ('a', 1)], 2)['slots'] == [(1, 'A'), (1, 'a')]
    # order: per_week, items type, size, then per row: shape, name, earliest, duplicate
    _raises(ValueError, PER, mod.schedule, 'bad', 'bad')
    _raises(TypeError, TYP, mod.schedule, L([]), 1)
    _raises(ValueError, SIZ, mod.schedule, [5] * 61, 1)
    _raises(ValueError, SHP, mod.schedule, [5, (None, 0)], 1)
    _raises(ValueError, NAM, mod.schedule, [(None, 0)], 1)
    _raises(ValueError, EAR, mod.schedule, [('a', 0), ('a', 1)], 1)
    _raises(ValueError, DUP, mod.schedule, [('a', 1), ('a', 1), (None, 0)], 1)
    _raises(ValueError, EAR, mod.schedule, [('a', 1), ('a', 9 * 10)], 1)


def test_inputs_unchanged_and_result_fresh():
    it = [('a', 1)]
    r = mod.schedule(it, 1)
    r['slots'].append(1)
    r['unscheduled'].append(1)
    assert it == [('a', 1)] and mod.schedule(it, 1)['slots'] == [(1, 'a')]
