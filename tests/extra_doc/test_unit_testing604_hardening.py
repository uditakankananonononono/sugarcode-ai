"""Row604 hardening: exact-type subclass pins, full-message pins, behavior
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

from sugarcode.extra_doc import unit_testing604 as mod

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
OK = ('ok', 2, 2)


def _oracle(rows):
    res = [(t, a == e, a, e) for t, a, e in sorted(rows, key=lambda r: r[0])]
    return {'results': res,
            'passed': sum(1 for r in res if r[1]),
            'failed': sum(1 for r in res if not r[1])}


def _core(m):
    run = m.compare_results
    # literal example: sorted by test id, echo positions, counts
    assert run([('pass', 2, 2), ('fail', 1, 3)]) == {
        'results': [('fail', False, 1, 3), ('pass', True, 2, 2)], 'passed': 1, 'failed': 1}
    assert run([('a', -1, 1)])['results'] == [('a', False, -1, 1)]
    # sorted output order, not input order
    assert [r[0] for r in run([('b', 0, 0), ('a', 0, 0)])['results']] == ['a', 'b']
    # boundary accepts
    assert run([('a', -1000000, 1000000)])['failed'] == 1
    assert run([('a' * 24, 1000000, 1000000)])['passed'] == 1
    assert len(run([('c%02d' % i, i, i) for i in range(32)])['results']) == 32
    # seeded random oracle
    rng = random.Random(604)
    for _ in range(200):
        n = rng.randint(1, 32)
        ids = rng.sample(['t%02d' % i for i in range(40)], n)
        rows = [(t, rng.randint(-1000000, 1000000), 0) for t in ids]
        rows = [(t, a, a if rng.random() < 0.5 else rng.randint(-1000000, 1000000)) for t, a, _ in rows]
        assert run(rows) == _oracle(rows)
    # full exact error messages
    for bad in (None, (), True, {}, 'x', 1, 1.0, iter([])):
        _raises(TypeError, 'exact list required', run, bad)
    _raises(ValueError, 'row count must be 1..32', run, [])
    _raises(ValueError, 'row count must be 1..32', run, [None] * 33)  # cap before any row scan
    for bad in (None, [], {}, 'x', 1, True, {1}):
        _raises(TypeError, 'exact tuple row required', run, [bad])
    for bad in ((), (None,) * 2, (None,) * 4):
        _raises(ValueError, 'wrong row arity', run, [bad])
    for bad in (None, 1, True, 1.0, b'a', [], {}):
        _raises(TypeError, 'exact string label required', run, [(bad, 0, 0)])
    for bad in ('', 'A', 'a b', 'a' * 25, 'a\n', 'é', '1a', '_a', 'a-b'):
        _raises(ValueError, 'label must be 1..24 lowercase identifier characters', run, [(bad, 0, 0)])
    for slot in (1, 2):
        row = ['ok', 0, 0]
        for bad in (None, True, False, 1.0, '1', [], {}):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
        for bad in (-1000001, 1000001, 10 ** 1000):
            row[slot] = bad
            _raises(ValueError, 'integer outside declared range', run, [tuple(row)])
    _raises(ValueError, 'duplicate test', run, [OK, ('ok', 1, 2)])
    # validation of every row precedes the duplicate check
    _raises(ValueError, 'integer outside declared range', run, [('ok', 2000000, 0), ('ok', 0, 0)])


def _late(m):
    run = m.compare_results
    # exact-type refusals: subclass at every typed slot, with exact messages
    _raises(TypeError, 'exact list required', run, L([OK]))
    _raises(TypeError, 'exact tuple row required', run, [T(OK)])
    _raises(TypeError, 'exact tuple row required', run, [R3('ok', 0, 0)])
    _raises(TypeError, 'exact string label required', run, [(S('ok'), 0, 0)])
    for slot in (1, 2):
        row = ['ok', 0, 0]
        for bad in (I(5), LyingGe(5), WeirdNe(5), Color.RED):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
    # subclass refused before any cap or range check
    _raises(TypeError, 'exact list required', run, L([OK] * 33))
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', LyingGe(10 ** 30), 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, WeirdNe(10 ** 30))])
    # exact list-shaped / tuple-shaped / str / int acceptance counterparts
    assert run([tuple(('ok', int(5), int(5)))])['passed'] == 1
    assert run(list([OK]))['passed'] == 1
    assert run([('ok', -1000000, -1000000)])['passed'] == 1


def _sym(m):
    run = m.compare_results
    # subclass placement symmetry across both numeric slots and both row positions
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, I(1))])
    _raises(TypeError, 'exact tuple row required', run, [T(OK), OK])
    _raises(TypeError, 'exact tuple row required', run, [OK, T(OK)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 0), OK])
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
    ('low <= value <= high', 'low - 1 <= value <= high'),
    ('-1000000, 1000000', '-1000000, 1000001'),
    ('if len({x[0] for x in rows})!=len(rows)', 'if False'),
    ('sorted(rows)', 'rows'),
    ('actual==expected', 'actual!=expected'),
    ("'passed':sum(x[1] for x in results)", "'passed':sum(not x[1] for x in results)"),
    ("'failed':sum(not x[1] for x in results)", "'failed':sum(x[1] for x in results)"),
    ('(test,actual==expected,actual,expected)', '(test,actual==expected,expected,actual)'),
    ('exact string label required', 'exact str label required'),
    ('row count must be 1..32', 'row count must be 1xx32'),
    ('wrong row arity', 'wrong arity'),
    ('duplicate test', 'duplicate  test'),
    ("raise ValueError('integer outside declared range')", "raise ValueError('integer outside declared bounds')"),
    ('LABEL.fullmatch(value) is None', 'LABEL.fullmatch(value) is not None'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
