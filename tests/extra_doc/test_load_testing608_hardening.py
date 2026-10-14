"""Row608 hardening: exact-type subclass pins, full-message pins, behavior
oracle, boundary accepts, mutation sweep. Tests-only delta.

Note: the 24-char label cap is doubly guarded (len check plus regex
quantifier on the same line), so single-site mutations of either half are
equivalent mutants; the refusal itself is pinned by the 'a'*25 battery case.
"""
import enum
import pathlib
import random
import signal
import types
from collections import namedtuple
from fractions import Fraction

import pytest

from sugarcode.extra_doc import load_testing608 as mod

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


R3 = namedtuple('R3', 'a b c')
OK = ('ok', 0, 3)


def _oracle(rows):
    ordered = sorted(rows, key=lambda r: (r[1], r[0]))
    clock = 0
    trace = []
    for req, arr, dur in ordered:
        start = clock if clock > arr else arr
        fin = start + dur
        trace.append((req, arr, start, fin, start - arr))
        clock = fin
    waits = [t[4] for t in trace]
    return {'requests': trace, 'mean_wait_fraction': str(Fraction(sum(waits), len(waits))),
            'maximum_wait': max(waits), 'finish': clock}


def _core(m):
    run = m.simulate_load
    assert run([('a', 0, 3), ('b', 1, 2), ('c', 10, 1)]) == {
        'requests': [('a', 0, 0, 3, 0), ('b', 1, 3, 5, 2), ('c', 10, 10, 11, 0)],
        'mean_wait_fraction': '2/3', 'maximum_wait': 2, 'finish': 11}
    # tie on arrival breaks by id ascending; idle gap before late arrival
    assert run([('z', 2, 1), ('a', 2, 3), ('b', 3, 2)]) == {
        'requests': [('a', 2, 2, 5, 0), ('z', 2, 5, 6, 3), ('b', 3, 6, 8, 3)],
        'mean_wait_fraction': '2', 'maximum_wait': 3, 'finish': 8}
    # boundary accepts
    assert run([('a', 0, 1)])['finish'] == 1
    assert run([('a', 1000000, 1000000)])['finish'] == 2000000
    assert run([('a' * 24, 0, 1)])['maximum_wait'] == 0
    assert len(run([('r%02d' % i, 0, 1) for i in range(32)])['requests']) == 32
    # seeded random oracle, contention-heavy
    rng = random.Random(608)
    for _ in range(200):
        n = rng.randint(1, 32)
        ids = rng.sample(['t%02d' % i for i in range(40)], n)
        rows = [(t, rng.randint(0, 100), rng.randint(1, 20)) for t in ids]
        assert run(rows) == _oracle(rows)
    # full exact error messages
    for bad in (None, (), True, {}, 'x', 1, 1.0, iter([])):
        _raises(TypeError, 'exact list required', run, bad)
    _raises(ValueError, 'row count must be 1..32', run, [])
    _raises(ValueError, 'row count must be 1..32', run, [None] * 33)
    for bad in (None, [], {}, 'x', 1, True, {1}):
        _raises(TypeError, 'exact tuple row required', run, [bad])
    for bad in ((), (None,) * 2, (None,) * 4):
        _raises(ValueError, 'wrong row arity', run, [bad])
    for bad in (None, 1, True, 1.0, b'a', [], {}):
        _raises(TypeError, 'exact string label required', run, [(bad, 0, 1)])
    for bad in ('', 'A', 'a b', 'a' * 25, 'a\n', 'é', '1a', '_a', 'a-b'):
        _raises(ValueError, 'label must be 1..24 lowercase identifier characters', run, [(bad, 0, 1)])
    for slot, low in ((1, 0), (2, 1)):
        row = ['ok', 0, 1]
        for bad in (None, True, False, 1.0, '1', [], {}):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
        for bad in (low - 1, 1000001, 10 ** 1000):
            row[slot] = bad
            _raises(ValueError, 'integer outside declared range', run, [tuple(row)])
    _raises(ValueError, 'duplicate request', run, [OK, ('ok', 1, 1)])
    # validation of every row precedes the duplicate check
    _raises(ValueError, 'integer outside declared range', run, [('ok', -1, 1), ('ok', 0, 1)])


def _late(m):
    run = m.simulate_load
    _raises(TypeError, 'exact list required', run, L([OK]))
    _raises(TypeError, 'exact tuple row required', run, [T(OK)])
    _raises(TypeError, 'exact tuple row required', run, [R3('ok', 0, 1)])
    _raises(TypeError, 'exact string label required', run, [(S('ok'), 0, 1)])
    for slot in (1, 2):
        row = ['ok', 0, 1]
        for bad in (I(0 if slot == 1 else 1), LyingGe(1), WeirdNe(1), Color.RED):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
    _raises(TypeError, 'exact list required', run, L([OK] * 33))
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', LyingGe(10 ** 30), 1)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, WeirdNe(10 ** 30))])
    assert run([tuple(('ok', int(0), int(1)))])['finish'] == 1
    assert run(list([OK]))['finish'] == 3


def _sym(m):
    run = m.simulate_load
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 1)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, I(1))])
    _raises(TypeError, 'exact tuple row required', run, [T(OK), OK])
    _raises(TypeError, 'exact tuple row required', run, [OK, T(OK)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 1), OK])
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 0, I(1))])


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
    ('_integer(arrival, 0, 1000000)', '_integer(arrival, -1, 1000000)'),
    ('_integer(arrival, 0, 1000000)', '_integer(arrival, 0, 1000001)'),
    ('_integer(duration, 1, 1000000)', '_integer(duration, 0, 1000000)'),
    ('_integer(duration, 1, 1000000)', '_integer(duration, 1, 1000001)'),
        ('        _integer(arrival, 0, 1000000)', '        pass'),
    ('key=lambda x:(x[1],x[0])', 'key=lambda x:(x[1],)'),
    ('sorted(rows,key=lambda x:(x[1],x[0]))', 'sorted(rows)'),
    ('start=max(clock,arrival)', 'start=arrival'),
    ('start=max(clock,arrival)', 'start=clock'),
    ('finish=start+duration', 'finish=start+duration+1'),
    ('finish=start+duration', 'finish=start*duration'),
    ('trace.append((request,arrival,start,finish,start-arrival))',
     'trace.append((request,arrival,start,finish,finish-arrival))'),
    ('clock=finish', 'clock=start'),
    ('F(sum(waits),len(waits))', 'F(sum(waits),len(waits)+1)'),
    ("'maximum_wait':max(waits)", "'maximum_wait':min(waits)"),
    ("'finish':clock", "'finish':0"),
    ('if len({x[0] for x in rows})!=len(rows)', 'if False'),
    ('exact string label required', 'exact str label required'),
    ('row count must be 1..32', 'row count must be 1xx32'),
    ('duplicate request', 'duplicate  request'),
    ("raise ValueError('integer outside declared range')", "raise ValueError('integer outside declared bounds')"),
    ('LABEL.fullmatch(value) is None', 'LABEL.fullmatch(value) is not None'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
