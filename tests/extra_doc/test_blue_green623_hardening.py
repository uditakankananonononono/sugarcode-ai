"""Row623 hardening: exact-type subclass pins, full-message pins, truth-table
behavior oracle, non-adjacent-order and mixed-validity witnesses, boundary
accepts, mutation sweep. Tests-only delta.

Note: the 24-char label cap is doubly guarded (len check plus regex
quantifier on the same line), so single-site mutations of either half are
equivalent mutants; the refusal itself is pinned by the 'a'*25 battery case.
"""
import enum
import itertools
import pathlib
import random
import signal
import types
from collections import namedtuple

import pytest

from sugarcode.extra_doc import blue_green623 as mod

SRC = pathlib.Path(mod.__file__).read_text()


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


class I(int):
    pass


class LyingGe(int):
    def __ge__(self, other):
        return True

    def __le__(self, other):
        return True


class WeirdNe(int):
    def __ne__(self, other):
        return False

    def __eq__(self, other):
        return False


class Color(enum.IntEnum):
    RED = 1


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


R4 = namedtuple('R4', 'a b c d')
OK = ('ok', 0, 1, 1)


def _oracle(rows):
    outs = []
    for s, c, b, g in sorted(rows, key=lambda r: r[0]):
        dest = 1 - c
        health = (b, g)
        sw = health[dest] == 1
        final = dest if sw else c
        outs.append((s, c, final, sw, bool(health[final])))
    return {'switches': outs, 'blocked_count': sum(1 for o in outs if not o[3])}


def _core(m):
    run = m.plan_switches
    assert run([('a', 0, 1, 1), ('b', 1, 1, 0), ('c', 0, 0, 0)]) == {
        'switches': [('a', 0, 1, True, True), ('b', 1, 0, True, True), ('c', 0, 0, False, False)],
        'blocked_count': 1}
    # complete truth table with exact full results
    for c, b, g in itertools.product((0, 1), repeat=3):
        assert run([('case', c, b, g)]) == {'switches': _oracle([('case', c, b, g)])['switches'],
                                             'blocked_count': _oracle([('case', c, b, g)])['blocked_count']}
    # blocked switch keeps current route and reports the current route's health
    assert run([('x', 0, 1, 0)])['switches'] == [('x', 0, 0, False, True)]
    assert run([('x', 1, 0, 1)])['switches'] == [('x', 1, 1, False, True)]
    # blocked count discriminates: all-healthy rows give zero
    assert run([('h%d' % i, i % 2, 1, 1) for i in range(3)])['blocked_count'] == 0
    # boundary accepts
    assert run([('a' * 24, 1, 0, 1)])['switches'][0][3] is False
    assert len(run([('s%02d' % i, 0, 1, 1) for i in range(32)])['switches']) == 32
    # seeded random oracle
    rng = random.Random(623)
    for _ in range(200):
        n = rng.randint(1, 32)
        ids = rng.sample(['t%02d' % i for i in range(40)], n)
        rows = [(t, rng.randint(0, 1), rng.randint(0, 1), rng.randint(0, 1)) for t in ids]
        assert run(rows) == _oracle(rows)
    # full exact error messages
    for bad in (None, (), True, {}, 'x', 1, 1.0, iter([])):
        _raises(TypeError, 'exact list required', run, bad)
    _raises(ValueError, 'row count must be 1..32', run, [])
    _raises(ValueError, 'row count must be 1..32', run, [None] * 33)
    for bad in (None, [], {}, 'x', 1, True, {1}):
        _raises(TypeError, 'exact tuple row required', run, [bad])
    for bad in ((), (None,) * 3, (None,) * 5):
        _raises(ValueError, 'wrong row arity', run, [bad])
    for bad in (None, 1, True, 1.0, b'a', [], {}):
        _raises(TypeError, 'exact string label required', run, [(bad, 0, 0, 0)])
    for bad in ('', 'A', 'a b', 'a' * 25, 'a\n', 'é', '1a', '_a', 'a-b'):
        _raises(ValueError, 'label must be 1..24 lowercase identifier characters', run, [(bad, 0, 0, 0)])
    for slot in (1, 2, 3):
        row = ['ok', 0, 0, 0]
        for bad in (None, True, False, 1.0, '1', [], {}):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
        for bad in (-1, 2, 10 ** 1000):
            row[slot] = bad
            _raises(ValueError, 'integer outside declared range', run, [tuple(row)])
    _raises(ValueError, 'duplicate scenario', run, [OK, ('ok', 1, 1, 1)])


def _mix(m):
    run = m.plan_switches
    _raises(ValueError, 'duplicate scenario', run, [('a', 0, 0, 0), ('b', 0, 0, 0), ('c', 0, 0, 0), ('a', 0, 0, 0)])
    _raises(ValueError, 'integer outside declared range', run, [('a', 0, 0, 0), ('b', 0, 0, 0), ('c', -1, 0, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('a', 0, 0, 0), ('b', 'x', 0, 0), ('c', 0, 0, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 0, 0, 0), ('ok3', I(1), 0, 0)])
    _raises(TypeError, 'exact tuple row required', run, [OK, ('ok2', 0, 0, 0), T(('ok3', 0, 0, 0))])
    _raises(TypeError, 'exact string label required', run, [('a', 0, 0, 0), ('b', 0, 0, 0), (S('c'), 0, 0, 0)])
    _raises(ValueError, 'integer outside declared range', run, [('a', 0, 0, 0), ('b', 2, 0, 0), ('c', 0, 0, 0)])
    rows = [('r%d' % i, 0, 1, 1) for i in reversed(range(8))]
    assert [o[0] for o in run(rows)['switches']] == ['r%d' % i for i in range(8)]
    _raises(ValueError, 'integer outside declared range', run, [('ok', 2, 0, 0), ('ok', 0, 0, 0)])


def _late(m):
    run = m.plan_switches
    _raises(TypeError, 'exact list required', run, L([OK]))
    _raises(TypeError, 'exact tuple row required', run, [T(OK)])
    _raises(TypeError, 'exact tuple row required', run, [R4('ok', 0, 1, 1)])
    _raises(TypeError, 'exact string label required', run, [(S('ok'), 0, 1, 1)])
    for slot in (1, 2, 3):
        row = ['ok', 0, 1, 1]
        for bad in (I(1), LyingGe(1), WeirdNe(1), Color.RED):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
    _raises(TypeError, 'exact list required', run, L([OK] * 33))
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', LyingGe(10 ** 30), 0, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, 0, WeirdNe(10 ** 30))])
    assert run([tuple(('ok', int(0), int(1), int(1)))])['switches'][0][3] is True
    assert run(list([OK]))['blocked_count'] == 0


def _sym(m):
    run = m.plan_switches
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 0, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, 0, I(1))])
    _raises(TypeError, 'exact tuple row required', run, [T(OK), OK])
    _raises(TypeError, 'exact tuple row required', run, [OK, T(OK)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 0, 0), OK])
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 0, 0, I(1))])


def battery(m):
    _core(m)
    _mix(m)
    _late(m)
    _sym(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('type(rows) is not list', 'not isinstance(rows, list)'),
    ('type(row) is not tuple', 'not isinstance(row, tuple)'),
    ('type(value) is not str', 'not isinstance(value, str)'),
    ('type(value) is not int', 'not isinstance(value, int)'),
    ('1 <= len(rows) <= 32', '1 <= len(rows) <= 33'),
    ('1 <= len(rows) <= 32', '0 <= len(rows) <= 32'),
    ('len(row) != arity', 'len(row) != arity + 1'),
    (r'[a-z][a-z0-9_]{0,23}', r'[a-z0-9_]{0,23}'),
    ('low <= value <= high', 'low < value < high'),
    ('_integer(current, 0, 1)', '_integer(current, 0, 2)'),
    ('_integer(blue, 0, 1)', '_integer(blue, -1, 1)'),
    ('        _integer(green, 0, 1)', '        pass'),
    ('destination=1-current', 'destination=current'),
    ('health[destination]==1', 'health[destination]==0'),
    ('health[destination]==1', 'health[current]==1'),
    ('final=destination if switched else current', 'final=destination'),
    ('bool(health[final])', 'bool(health[destination])'),
    ('bool(health[final])', 'True'),
    ('outcomes.append((scenario,current,final,switched,bool(health[final])))',
     'outcomes.append((scenario,final,current,switched,bool(health[final])))'),
    ("'blocked_count':sum(not x[3] for x in outcomes)", "'blocked_count':sum(x[3] for x in outcomes)"),
    ("'blocked_count':sum(not x[3] for x in outcomes)", "'blocked_count':len(outcomes)"),
    ('for scenario,current,blue,green in sorted(rows)', 'for scenario,current,blue,green in rows'),
    ('if len({x[0] for x in rows})!=len(rows)', 'if False'),
    ('exact string label required', 'exact str label required'),
    ('row count must be 1..32', 'row count must be 1xx32'),
    ('duplicate scenario', 'duplicate  scenario'),
    ("raise ValueError('integer outside declared range')", "raise ValueError('integer outside declared bounds')"),
    ('LABEL.fullmatch(value) is None', 'LABEL.fullmatch(value) is not None'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
