import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import content_plan407 as mod

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



def T3(*rows):
    return list(rows)


def test_scope_and_constants():
    assert mod.SCOPE == 'PARTIAL: priority and effort ranking against a supplied budget, no real strategy'
    assert mod.NOT_CLAIMED == ('audience research', 'content quality', 'channel choice',
                               'real effort estimation', 'production readiness')
    assert 'NOT_CLAIMED' in mod.__doc__ and not (ROOT / '__init__.py').exists()
    assert (mod.MAX_TOPICS, mod.MAX_NAME, mod.MAX_CAPACITY, mod.MAX_SCORE) == (30, 40, 100, 5)


def _oracle(topics, capacity):
    """Independent: decorate-sort-undecorate with a running budget."""
    deco = sorted([(-p, e, i, n) for i, (n, p, e) in enumerate(topics)])
    planned, skipped, budget = [], [], capacity
    for _, e, _, n in deco:
        if budget - e >= 0:
            budget -= e
            planned.append(n)
        else:
            skipped.append(n)
    return {'planned': planned, 'skipped': skipped, 'spent': sum(e for n, p, e in topics if n in planned)}


def test_ranking_and_budget():
    t = [('a', 3, 2), ('b', 5, 4), ('c', 5, 1), ('d', 1, 1)]
    assert mod.plan(t, 5) == {'planned': ['c', 'b'], 'skipped': ['a', 'd'], 'spent': 5}
    assert mod.plan(t, 100) == {'planned': ['c', 'b', 'a', 'd'], 'skipped': [], 'spent': 8}
    assert mod.plan(t, 0) == {'planned': [], 'skipped': ['c', 'b', 'a', 'd'], 'spent': 0}
    # the walk continues past a skipped topic
    assert mod.plan([('big', 5, 5), ('small', 4, 1)], 3) == {'planned': ['small'], 'skipped': ['big'], 'spent': 1}
    # an exact fit is planned
    assert mod.plan([('x', 1, 5)], 5) == {'planned': ['x'], 'skipped': [], 'spent': 5}
    assert mod.plan([('x', 1, 5)], 4)['skipped'] == ['x']
    # priority ties: lower effort first, then supplied order
    assert mod.plan([('p', 2, 3), ('q', 2, 1), ('r', 2, 3)], 100)['planned'] == ['q', 'p', 'r']
    assert mod.plan([('r', 2, 3), ('p', 2, 3)], 100)['planned'] == ['r', 'p']
    # priority beats low effort
    assert mod.plan([('lo', 1, 1), ('hi', 2, 5)], 100)['planned'] == ['hi', 'lo']
    # tuples and lists accepted
    assert mod.plan((('a', 1, 1),), 1)['planned'] == ['a'] and mod.plan([['a', 1, 1]], 1)['planned'] == ['a']


def test_randomized_against_oracle():
    rng = random.Random(407)
    for _ in range(500):
        n = rng.randint(1, 12)
        topics = [('t%d' % i, rng.randint(1, 5), rng.randint(1, 5)) for i in range(n)]
        cap = rng.randint(0, 40)
        assert mod.plan(topics, cap) == _oracle(topics, cap)


def test_validation_messages_boundaries_and_order():
    CAP = 'capacity must be a nonbool int from 0 to 100'
    TYP = 'topics must be a list or tuple'
    SIZ = 'topics must hold 1 to 30 rows'
    SHP = 'each topic must be a (name, priority, effort) list or tuple'
    NAM = 'names must be str of 1 to 40 characters'
    PRI = 'priority must be a nonbool int from 1 to 5'
    EFF = 'effort must be a nonbool int from 1 to 5'
    DUP = 'names must be distinct'
    ok = [('a', 1, 1)]
    for bad in (-1, 101, True, False, 1.0, '1', None, I(1), 10 ** 30):
        _raises(ValueError, CAP, mod.plan, ok, bad)
    assert mod.plan(ok, 0)['spent'] == 0 and mod.plan(ok, 100)['spent'] == 1
    for bad in (None, 'ab', 5, {}, L(ok), T(ok)):
        _raises(TypeError, TYP, mod.plan, bad, 1)
    _raises(ValueError, SIZ, mod.plan, [], 1)
    _raises(ValueError, SIZ, mod.plan, [('t%d' % i, 1, 1) for i in range(31)], 1)
    assert len(mod.plan([('t%d' % i, 1, 1) for i in range(30)], 100)['planned']) == 30
    for bad in (None, 5, 'abc', ('a', 1), ('a', 1, 1, 1), (), L(['a', 1, 1]), T(['a', 1, 1]), {'a': 1}):
        _raises(ValueError, SHP, mod.plan, [bad], 1)
    for bad in ('', 'x' * 41, None, 5, b'a', S('a'), ['a']):
        _raises(ValueError, NAM, mod.plan, [(bad, 1, 1)], 1)
    assert mod.plan([('x' * 40, 1, 1)], 1)['planned'] == ['x' * 40] and mod.plan([('x', 1, 1)], 1)['spent'] == 1
    for bad in (0, 6, True, False, 1.0, '1', None, I(1), 10 ** 30):
        _raises(ValueError, PRI, mod.plan, [('a', bad, 1)], 1)
        _raises(ValueError, EFF, mod.plan, [('a', 1, bad)], 1)
    assert mod.plan([('a', 5, 5)], 5)['planned'] == ['a']
    _raises(ValueError, DUP, mod.plan, [('a', 1, 1), ('a', 2, 2)], 1)
    assert mod.plan([('a', 1, 1), ('A', 1, 1)], 2)['planned'] == ['a', 'A']
    assert mod.plan([('A', 1, 1), ('a', 1, 1)], 2)['planned'] == ['A', 'a']
    # order: capacity, topics type, size, then per row: shape, name, priority, effort, duplicate
    _raises(ValueError, CAP, mod.plan, 'bad', 'bad')
    _raises(TypeError, TYP, mod.plan, L([]), 1)
    _raises(ValueError, SIZ, mod.plan, [5] * 31, 1)
    _raises(ValueError, SHP, mod.plan, [5, (None, 0, 0)], 1)
    _raises(ValueError, NAM, mod.plan, [(None, 0, 0)], 1)
    _raises(ValueError, PRI, mod.plan, [('a', 0, 0)], 1)
    _raises(ValueError, EFF, mod.plan, [('a', 1, 0), ('a', 1, 1)], 1)
    _raises(ValueError, DUP, mod.plan, [('a', 1, 1), ('a', 1, 1), (None, 0, 0)], 1)
    _raises(ValueError, PRI, mod.plan, [('a', 1, 1), ('a', 9, 1)], 1)


def test_inputs_unchanged_and_result_fresh():
    t = [('a', 1, 1), ('b', 2, 1)]
    r = mod.plan(t, 5)
    r['planned'].append('z')
    assert t == [('a', 1, 1), ('b', 2, 1)] and mod.plan(t, 5)['planned'] == ['b', 'a']
