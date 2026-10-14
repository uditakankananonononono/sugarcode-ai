"""Row603 hardening: exact-type subclass pins, full-message pins, behavior
oracle, boundary accepts, mutation sweep. Tests-only delta."""
import enum
import pathlib
import random
import signal
import types
from collections import namedtuple

import pytest

from sugarcode.extra_doc import property_testing603 as mod

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

    def __gt__(self, other):
        return True

    def __lt__(self, other):
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
OK = ('ok', [2, 1, 1], [1, 1, 2])


def _oracle(rows):
    out = []
    for case, original, output in sorted(rows, key=lambda r: r[0]):
        f = []
        if len(original) != len(output):
            f.append('length')
        if sorted(original) != sorted(output):
            f.append('multiplicity')
        if list(output) != sorted(output):
            f.append('order')
        out.append((case, f))
    return {'cases': out, 'failed_cases': sum(1 for _, f in out if f)}


def _core(m):
    run = m.check_sort_properties
    # literal example: each property reported independently, cases sorted by id
    rows = [('good', [2, 1, 1], [1, 1, 2]), ('empty', [], []), ('order', [1, 2], [2, 1]),
            ('mult', [1, 1], [1, 2]), ('length', [1], [1, 1])]
    assert run(rows) == {'cases': [('empty', []), ('good', []), ('length', ['length', 'multiplicity']),
                                   ('mult', ['multiplicity']), ('order', ['order'])],
                         'failed_cases': 3}
    # failure list order is length before multiplicity
    assert run([('x', [1], [1, 1])])['cases'] == [('x', ['length', 'multiplicity'])]
    # sorted output order, not input order
    r = run([('b', [1], [1]), ('a', [1], [1])])
    assert [c for c, _ in r['cases']] == ['a', 'b']
    # failed_cases counts cases, not individual failures
    assert run([('x', [1], [2, 2])])['failed_cases'] == 1
    # boundary accepts
    assert run([('a', [], [])])['failed_cases'] == 0
    assert run([('a' * 24, [-1000, 1000], [-1000, 1000])])['failed_cases'] == 0
    assert run([('c', list(range(16)), list(range(16)))])['failed_cases'] == 0
    assert len(run([('c%02d' % i, [], []) for i in range(32)])['cases']) == 32
    # seeded random oracle on shuffled valid inputs, correct and perturbed
    rng = random.Random(603)
    for _ in range(200):
        n = rng.randint(0, 16)
        original = [rng.randint(-1000, 1000) for _ in range(n)]
        output = sorted(original)
        if n >= 2 and rng.random() < 0.5:
            i, j = rng.randrange(n), rng.randrange(n)
            output[i], output[j] = output[j], output[i]
        if n < 16 and rng.random() < 0.3:
            output = output + [rng.randint(-1000, 1000)]
        rows = [('z' if rng.random() < 0.5 else 'a', original, output)]
        assert run(rows) == _oracle(rows)
    # full exact error messages
    for bad in (None, (), True, {}, 'x', 1, 1.0):
        _raises(TypeError, 'exact case list required', run, bad)
    _raises(ValueError, 'case count must be 1..32', run, [])
    _raises(ValueError, 'case count must be 1..32', run, [OK] * 33)
    _raises(ValueError, 'case count must be 1..32', run, [None] * 33)  # cap before any row
    for bad in ([None, None, None], None, True, {}, 'case', 1, {1, 2}):
        _raises(TypeError, 'exact tuple case required', run, [bad])
    for bad in ((), (None,) * 2, (None,) * 4):
        _raises(ValueError, 'case arity must be three', run, [bad])
    for bad in (None, True, 1, 1.0, b'a', [], {}):
        _raises(TypeError, 'exact case identifier string required', run, [(bad, [], [])])
    for bad in ('', 'A', 'a b', 'a' * 25, '1a', '_a', 'a-b', 'aA'):
        _raises(ValueError, 'bounded lowercase case identifier required', run, [(bad, [], [])])
    for slot in (1, 2):
        row = ['case', [], []]
        for bad in (None, (), True, {}, 'x', 1):
            row[slot] = bad
            _raises(TypeError, 'exact integer list required', run, [tuple(row)])
        row[slot] = [None] * 17
        _raises(ValueError, 'integer list cap must be at most16', run, [tuple(row)])  # cap before elements
        for bad in (None, True, 1.0, '1', [], {}):
            row[slot] = [bad]
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
        for bad in (-1001, 1001):
            row[slot] = [bad]
            _raises(ValueError, 'integer outside declared range', run, [tuple(row)])
        row[slot] = []
    _raises(ValueError, 'duplicate case', run, [('a', [], []), ('a', [1], [1])])
    # validation of every row precedes the duplicate check
    _raises(ValueError, 'integer outside declared range', run, [('a', [], []), ('a', [2000], [2000])])


def _late(m):
    run = m.check_sort_properties
    # exact-type refusals: subclass at every typed slot, with exact messages
    _raises(TypeError, 'exact case list required', run, L([OK]))
    _raises(TypeError, 'exact tuple case required', run, [T(OK)])
    _raises(TypeError, 'exact tuple case required', run, [R3('ok', [], [])])
    _raises(TypeError, 'exact case identifier string required', run, [(S('ok'), [], [])])
    for slot in (1, 2):
        row = ['ok', [], []]
        row[slot] = L([1])
        _raises(TypeError, 'exact integer list required', run, [tuple(row)])
        for bad in (I(5), LyingGe(5), WeirdNe(5), Color.RED):
            row[slot] = [bad]
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
    # subclass refused before any cap or range check
    _raises(TypeError, 'exact case list required', run, L([OK] * 33))
    _raises(TypeError, 'exact integer list required', run, [('ok', L([0] * 17), [])])
    _raises(TypeError, 'exact integer list required', run, [('ok', [], L([0] * 17))])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', [LyingGe(10 ** 30)], [])])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', [], [WeirdNe(10 ** 30)])])
    # exact list-shaped / tuple-shaped / str / int acceptance counterparts
    good = run([('ok', list([2, 1]), list([1, 2]))])
    assert good['failed_cases'] == 0
    assert run([tuple(('ok', [], []))])['failed_cases'] == 0
    assert run([('ok', [int(5)], [int(5)])])['failed_cases'] == 0


def _sym(m):
    run = m.check_sort_properties
    # subclass placement symmetry across both list slots and both row positions
    _raises(TypeError, 'exact integer list required', run, [('ok', L([]), [])])
    _raises(TypeError, 'exact integer list required', run, [('ok', [], L([]))])
    _raises(TypeError, 'exact tuple case required', run, [T(OK), OK])
    _raises(TypeError, 'exact tuple case required', run, [OK, T(OK)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', [I(1)], []), OK])
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', [], [I(1)])])


def battery(m):
    _core(m)
    _late(m)
    _sym(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('type(rows) is not list', 'not isinstance(rows, list)'),
    ('type(row) is not tuple', 'not isinstance(row, tuple)'),
    ('type(case) is not str', 'not isinstance(case, str)'),
    ('type(values) is not list', 'not isinstance(values, list)'),
    ('type(value) is not int', 'not isinstance(value, int)'),
    ('if not 1<=len(rows)<=32', 'if not 1<=len(rows)<=33'),
    ('if not 1<=len(rows)<=32', 'if not 0<=len(rows)<=32'),
    ('len(values)>16', 'len(values)>17'),
    ('not -1000<=value<=1000', 'not -1001<=value<=1000'),
    ('not -1000<=value<=1000', 'not -1000<=value<=1001'),
    ('1<=len(case)<=24', '1<=len(case)<=25'),
    ('1<=len(case)<=24', '2<=len(case)<=24'),
    (r"[a-z][a-z0-9_]*", r"[a-z0-9_]*"),
    (r"[a-z][a-z0-9_]*", r"[a-z][a-z0-9_]+"),
    ('len(row)!=3', 'len(row)!=4'),
    ("raise ValueError('duplicate case')", "pass"),
    ('len({x[0] for x in rows})!=len(rows)', 'False'),
    ('for case,original,output in sorted(rows)', 'for case,original,output in rows'),
    ("failures.append('length')", "pass  #"),
    ('Counter(original)!=Counter(output)', 'list(original)!=list(output)'),
    ('output[i]>output[i+1]', 'output[i]>=output[i+1]'),
    ('if any(output[i]>output[i+1] for i in range(len(output)-1))', 'if False'),
    ('sum(bool(failures) for _,failures in results)', 'sum(len(failures) for _,failures in results)'),
    ('for values in (original,output)', 'for values in (original,)'),
    ('case count must be 1..32', 'case count must be 1xx32'),
    ('exact nonbool integer required', 'exact non-bool integer required'),
    ('integer list cap must be at most16', 'integer list cap must be at most 16'),
    ('duplicate case', 'Duplicate case'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
