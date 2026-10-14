"""Row605 hardening: exact-type subclass pins, full-message pins, behavior
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

import pytest

from sugarcode.extra_doc import integration_testing605 as mod

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


R5 = namedtuple('R5', 'a b c d e')
OK = ('ok', 3, 2, 1, 7)


def _oracle(rows):
    res = []
    for case, value, multiplier, offset, expected in sorted(rows, key=lambda r: r[0]):
        # independent composition: repeated addition, no * operator
        inter = sum(value for _ in range(abs(multiplier))) * (-1 if multiplier < 0 else 1)
        actual = inter + offset
        res.append((case, inter, actual, expected, actual == expected))
    return {'cases': res, 'failed': sum(1 for r in res if not r[4])}


def _core(m):
    run = m.exercise_composition
    assert run([('a', 3, 2, 1, 7), ('b', -2, 4, 3, 0)]) == {
        'cases': [('a', 6, 7, 7, True), ('b', -8, -5, 0, False)], 'failed': 1}
    assert run([('a', 2, 3, 4, 18)])['failed'] == 1
    assert [r[0] for r in run([('b', 0, 0, 0, 0), ('a', 0, 0, 0, 0)])['cases']] == ['a', 'b']
    # boundary accepts, including max intermediate overflowing the operand range
    assert run([('a', -1000, -1000, -1000, 999000)])['cases'][0] == ('a', 1000000, 999000, 999000, True)
    assert run([('a', 1000, 1000, 1000, 1001000)])['cases'][0][4] is True
    assert run([('a', 0, 0, 0, 2000000)])['failed'] == 1
    assert run([('a', 0, 0, 0, -2000000)])['failed'] == 1
    assert run([('a' * 24, 0, 0, 0, 0)])['failed'] == 0
    assert len(run([('c%02d' % i, 0, 1, 0, 0) for i in range(32)])['cases']) == 32
    # seeded random oracle
    rng = random.Random(605)
    for _ in range(200):
        n = rng.randint(1, 32)
        ids = rng.sample(['t%02d' % i for i in range(40)], n)
        rows = [(t, rng.randint(-1000, 1000), rng.randint(-1000, 1000), rng.randint(-1000, 1000), 0)
                for t in ids]
        rows = [(t, v, k, o, v * k + o if rng.random() < 0.5 else rng.randint(-2000000, 2000000))
                for t, v, k, o, _e in rows]
        assert run(rows) == _oracle(rows)
    # full exact error messages
    for bad in (None, (), True, {}, 'x', 1, 1.0, iter([])):
        _raises(TypeError, 'exact list required', run, bad)
    _raises(ValueError, 'row count must be 1..32', run, [])
    _raises(ValueError, 'row count must be 1..32', run, [None] * 33)
    for bad in (None, [], {}, 'x', 1, True, {1}):
        _raises(TypeError, 'exact tuple row required', run, [bad])
    for bad in ((), (None,) * 4, (None,) * 6):
        _raises(ValueError, 'wrong row arity', run, [bad])
    for bad in (None, 1, True, 1.0, b'a', [], {}):
        _raises(TypeError, 'exact string label required', run, [(bad, 0, 0, 0, 0)])
    for bad in ('', 'A', 'a b', 'a' * 25, 'a\n', 'é', '1a', '_a', 'a-b'):
        _raises(ValueError, 'label must be 1..24 lowercase identifier characters', run, [(bad, 0, 0, 0, 0)])
    for slot in (1, 2, 3, 4):
        row = ['ok', 0, 0, 0, 0]
        for bad in (None, True, False, 1.0, '1', [], {}):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
        limit = 1000 if slot < 4 else 2000000
        for bad in (-limit - 1, limit + 1, 10 ** 1000):
            row[slot] = bad
            _raises(ValueError, 'integer outside declared range', run, [tuple(row)])
    _raises(ValueError, 'duplicate case', run, [OK, ('ok', 0, 0, 0, 0)])
    _raises(ValueError, 'integer outside declared range', run, [('ok', 0, 0, 0, 3000000), ('ok', 0, 0, 0, 0)])


def _late(m):
    run = m.exercise_composition
    _raises(TypeError, 'exact list required', run, L([OK]))
    _raises(TypeError, 'exact tuple row required', run, [T(OK)])
    _raises(TypeError, 'exact tuple row required', run, [R5('ok', 0, 0, 0, 0)])
    _raises(TypeError, 'exact string label required', run, [(S('ok'), 0, 0, 0, 0)])
    for slot in (1, 2, 3, 4):
        row = ['ok', 0, 0, 0, 0]
        for bad in (I(5), LyingGe(5), WeirdNe(5), Color.RED):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
    _raises(TypeError, 'exact list required', run, L([OK] * 33))
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', LyingGe(10 ** 30), 0, 0, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, 0, 0, WeirdNe(10 ** 30))])
    assert run([tuple(('ok', int(3), int(2), int(1), int(7)))])['failed'] == 0
    assert run(list([OK]))['failed'] == 0


def _sym(m):
    run = m.exercise_composition
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 0, 0, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, 0, 0, I(1))])
    _raises(TypeError, 'exact tuple row required', run, [T(OK), OK])
    _raises(TypeError, 'exact tuple row required', run, [OK, T(OK)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 0, 0, 0), OK])
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 0, 0, 0, I(1))])


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
    ('_integer(operand, -1000, 1000)', '_integer(operand, -1000, 1001)'),
    ('_integer(operand, -1000, 1000)', '_integer(operand, -1001, 1000)'),
    ('_integer(expected, -2000000, 2000000)', '_integer(expected, -2000000, 2000001)'),
    ('for operand in (value,multiplier,offset)', 'for operand in (value,multiplier)'),
    ('if len({x[0] for x in rows}) != len(rows)', 'if False'),
    ('for case,value,multiplier,offset,expected in sorted(rows)',
     'for case,value,multiplier,offset,expected in rows'),
    ('return value*multiplier', 'return value+multiplier'),
    ('return value+offset', 'return value-offset'),
    ('actual=add(intermediate,offset)', 'actual=multiply(intermediate,offset)'),
    ('intermediate=multiply(value,multiplier)', 'intermediate=multiply(multiplier,value)+1'),
    ('actual==expected', 'actual!=expected'),
    ("'failed':sum(not x[4] for x in results)", "'failed':sum(x[4] for x in results)"),
    ('(case,intermediate,actual,expected,actual==expected)',
     '(case,actual,intermediate,expected,actual==expected)'),
    ('exact string label required', 'exact str label required'),
    ('row count must be 1..32', 'row count must be 1xx32'),
    ('duplicate case', 'duplicate  case'),
    ("raise ValueError('integer outside declared range')", "raise ValueError('integer outside declared bounds')"),
    ('LABEL.fullmatch(value) is None', 'LABEL.fullmatch(value) is not None'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
