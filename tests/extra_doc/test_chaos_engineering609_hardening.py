"""Row609 hardening: exact-type subclass pins, full-message pins, truth-table
behavior oracle, boundary accepts, mutation sweep. Tests-only delta.

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

from sugarcode.extra_doc import chaos_engineering609 as mod

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
OK = ('ok', 0, 1, 0)


def _oracle(rows):
    outs = []
    for s, p, b, f in sorted(rows, key=lambda r: r[0]):
        route = 'primary' if p == 0 else ('backup' if (f, b) == (1, 0) else 'unavailable')
        outs.append((s, route))
    return {'outcomes': outs, 'unavailable': sum(1 for _, r in outs if r == 'unavailable')}


def _core(m):
    run = m.simulate_failover
    assert run([('a', 0, 1, 0), ('b', 1, 0, 1), ('c', 1, 1, 1)]) == {
        'outcomes': [('a', 'primary'), ('b', 'backup'), ('c', 'unavailable')], 'unavailable': 1}
    # complete truth table with exact full results
    for p, b, f in itertools.product((0, 1), repeat=3):
        expected = 'primary' if p == 0 else ('backup' if (f, b) == (1, 0) else 'unavailable')
        assert run([('case', p, b, f)]) == {'outcomes': [('case', expected)],
                                             'unavailable': int(expected == 'unavailable')}
    # count distinguishes routes: zero unavailable with healthy primaries present
    assert run([('h%d' % i, 0, 0, 0) for i in range(3)])['unavailable'] == 0
    # sorted output order, not input order
    assert [o[0] for o in run([('b', 0, 0, 0), ('a', 0, 0, 0)])['outcomes']] == ['a', 'b']
    # boundary accepts
    assert run([('a' * 24, 1, 0, 1)])['outcomes'] == [('a' * 24, 'backup')]
    assert len(run([('s%02d' % i, 0, 0, 0) for i in range(32)])['outcomes']) == 32
    # seeded random oracle over multi-row scenarios
    rng = random.Random(609)
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
    # validation of every row precedes the duplicate check
    _raises(ValueError, 'integer outside declared range', run, [('ok', 2, 0, 0), ('ok', 0, 0, 0)])


def _late(m):
    run = m.simulate_failover
    _raises(TypeError, 'exact list required', run, L([OK]))
    _raises(TypeError, 'exact tuple row required', run, [T(OK)])
    _raises(TypeError, 'exact tuple row required', run, [R4('ok', 0, 0, 0)])
    _raises(TypeError, 'exact string label required', run, [(S('ok'), 0, 0, 0)])
    for slot in (1, 2, 3):
        row = ['ok', 0, 0, 0]
        for bad in (I(1), LyingGe(1), WeirdNe(1), Color.RED):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
    _raises(TypeError, 'exact list required', run, L([OK] * 33))
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', LyingGe(10 ** 30), 0, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, 0, WeirdNe(10 ** 30))])
    assert run([tuple(('ok', int(1), int(0), int(1)))])['outcomes'] == [('ok', 'backup')]
    assert run(list([OK]))['outcomes'] == [('ok', 'primary')]


def _sym(m):
    run = m.simulate_failover
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 0, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, 0, I(1))])
    _raises(TypeError, 'exact tuple row required', run, [T(OK), OK])
    _raises(TypeError, 'exact tuple row required', run, [OK, T(OK)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 0, 0), OK])
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 0, 0, I(1))])


def battery(m):
    _core(m)
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
    ('_integer(primary_failed, 0, 1)', '_integer(primary_failed, 0, 2)'),
    ('_integer(backup_failed, 0, 1)', '_integer(backup_failed, -1, 1)'),
    ('_integer(failover, 0, 1)', 'pass'),
    ('primary_failed==0', 'primary_failed!=0'),
    ('failover==1 and backup_failed==0', 'failover==1 or backup_failed==0'),
    ('failover==1 and backup_failed==0', 'failover==0 and backup_failed==0'),
    ('failover==1 and backup_failed==0', 'failover==1'),
    ("route='primary'", "route='backup'"),
    ("route='backup'", "route='primary'"),
    ("route='unavailable'", "route='down'"),
    ('outcomes.append((scenario,route))', 'outcomes.append((route,scenario))'),
    ("sum(route=='unavailable' for _,route in outcomes)", "sum(route=='primary' for _,route in outcomes)"),
    ("sum(route=='unavailable' for _,route in outcomes)", "sum(route!='unavailable' for _,route in outcomes)"),
    ('for scenario,primary_failed,backup_failed,failover in sorted(rows)',
     'for scenario,primary_failed,backup_failed,failover in rows'),
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
