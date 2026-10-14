"""Row626 hardening: exact-type subclass pins, full-message pins, behavior
oracle, non-adjacent-order and mixed-validity witnesses, boundary accepts,
mutation sweep. Tests-only delta.

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

import pytest

from sugarcode.extra_doc import dark_launching626 as mod

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
OK = ('ok', 3, 1)


def _oracle(rows):
    exp, diag = [], []
    for r, v, e in sorted(rows, key=lambda x: x[0]):
        s = v + v  # doubling without the * operator
        exp.append((r, s))
        if e == 1:
            c = s + 1
            diag.append((r, c, c - s))
    return {'exposed': exp, 'diagnostics': diag, 'dark_execution_count': len(diag)}


def _core(m):
    run = m.simulate_dark_launch
    assert run([('a', 3, 1), ('b', -2, 0), ('c', 0, 1)]) == {
        'exposed': [('a', 6), ('b', -4), ('c', 0)],
        'diagnostics': [('a', 7, 1), ('c', 1, 1)], 'dark_execution_count': 2}
    # flag never changes exposure; disabled rows leave no diagnostic trace
    for value, stable, candidate in [(-1000000, -2000000, -1999999), (0, 0, 1), (1000000, 2000000, 2000001)]:
        assert run([('r', value, 0)]) == {'exposed': [('r', stable)], 'diagnostics': [],
                                           'dark_execution_count': 0}
        assert run([('r', value, 1)]) == {'exposed': [('r', stable)],
                                           'diagnostics': [('r', candidate, 1)], 'dark_execution_count': 1}
    # candidate delta is exactly 1
    assert run([('r', -7, 1)])['diagnostics'] == [('r', -13, 1)]
    # boundary accepts
    assert run([('a' * 24, 1000000, 1)])['dark_execution_count'] == 1
    assert len(run([('r%02d' % i, 0, 0) for i in range(32)])['exposed']) == 32
    # seeded random oracle
    rng = random.Random(626)
    for _ in range(200):
        n = rng.randint(1, 32)
        ids = rng.sample(['t%02d' % i for i in range(40)], n)
        rows = [(t, rng.randint(-1000000, 1000000), rng.randint(0, 1)) for t in ids]
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
        _raises(TypeError, 'exact string label required', run, [(bad, 0, 0)])
    for bad in ('', 'A', 'a b', 'a' * 25, 'a\n', 'é', '1a', '_a', 'a-b'):
        _raises(ValueError, 'label must be 1..24 lowercase identifier characters', run, [(bad, 0, 0)])
    for slot, low, high in ((1, -1000000, 1000000), (2, 0, 1)):
        row = ['ok', 0, 0]
        for bad in (None, True, False, 1.0, '1', [], {}):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
        for bad in (low - 1, high + 1, 10 ** 1000):
            row[slot] = bad
            _raises(ValueError, 'integer outside declared range', run, [tuple(row)])
    _raises(ValueError, 'duplicate request', run, [OK, ('ok', 0, 0)])


def _mix(m):
    run = m.simulate_dark_launch
    _raises(ValueError, 'duplicate request', run, [('a', 0, 0), ('b', 0, 0), ('c', 0, 0), ('a', 0, 0)])
    _raises(ValueError, 'integer outside declared range', run, [('a', 0, 0), ('b', 0, 0), ('c', 1000001, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('a', 0, 0), ('b', 'x', 0), ('c', 0, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 0, 0), ('ok3', I(1), 0)])
    _raises(TypeError, 'exact tuple row required', run, [OK, ('ok2', 0, 0), T(('ok3', 0, 0))])
    _raises(TypeError, 'exact string label required', run, [('a', 0, 0), ('b', 0, 0), (S('c'), 0, 0)])
    _raises(ValueError, 'integer outside declared range', run, [('a', 0, 0), ('b', 0, 2), ('c', 0, 0)])
    rows = [('r%d' % i, 1, 1) for i in reversed(range(8))]
    assert [e[0] for e in run(rows)['exposed']] == ['r%d' % i for i in range(8)]
    _raises(ValueError, 'integer outside declared range', run, [('ok', 2000000, 0), ('ok', 0, 0)])


def _late(m):
    run = m.simulate_dark_launch
    _raises(TypeError, 'exact list required', run, L([OK]))
    _raises(TypeError, 'exact tuple row required', run, [T(OK)])
    _raises(TypeError, 'exact tuple row required', run, [R3('ok', 3, 1)])
    _raises(TypeError, 'exact string label required', run, [(S('ok'), 3, 1)])
    for slot, good in ((1, 3), (2, 1)):
        row = ['ok', 3, 1]
        for bad in (I(good), LyingGe(good), WeirdNe(good), Color.RED):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
    _raises(TypeError, 'exact list required', run, L([OK] * 33))
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', LyingGe(10 ** 30), 1)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, WeirdNe(10 ** 30))])
    assert run([tuple(('ok', int(3), int(1)))])['exposed'] == [('ok', 6)]
    assert run(list([OK]))['dark_execution_count'] == 1


def _sym(m):
    run = m.simulate_dark_launch
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, I(1))])
    _raises(TypeError, 'exact tuple row required', run, [T(OK), OK])
    _raises(TypeError, 'exact tuple row required', run, [OK, T(OK)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 0), OK])
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 0, I(1))])


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
    ('_integer(value, -1000000, 1000000)', '_integer(value, -1000001, 1000000)'),
    ('_integer(value, -1000000, 1000000)', '_integer(value, -1000000, 1000001)'),
    ('_integer(enabled, 0, 1)', '_integer(enabled, 0, 2)'),
    ('        _integer(value, -1000000, 1000000)', '        pass'),
    ('stable=2*value', 'stable=3*value'),
    ('stable=2*value', 'stable=2*value+1'),
    ('candidate=2*value+1', 'candidate=2*value'),
    ('candidate=2*value+1', 'candidate=2*value+2'),
    ('if enabled==1', 'if enabled==0'),
    ('if enabled==1', 'if True'),
    ('exposed.append((request,stable))', 'exposed.append((request,value))'),
    ('diagnostics.append((request,candidate,candidate-stable))',
     'diagnostics.append((request,candidate,candidate))'),
    ("'dark_execution_count':len(diagnostics)", "'dark_execution_count':len(exposed)"),
    ('for request,value,enabled in sorted(rows)', 'for request,value,enabled in rows'),
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
