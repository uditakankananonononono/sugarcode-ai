"""Row621 hardening: exact-type subclass pins, full-message pins, behavior
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

from sugarcode.extra_doc import quota_management621 as mod

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
OK = ('ok', 30, 20)


def _oracle(rows):
    alloc = sum(r[1] for r in rows)
    cons = []
    for c, a, q in sorted(rows, key=lambda r: r[0]):
        ok = q <= a
        used = q if ok else 0
        cons.append((c, ok, used, a - used))
    return {'consumers': cons, 'allocated': alloc, 'unallocated': 100 - alloc,
            'used': sum(c[2] for c in cons)}


def _core(m):
    run = m.evaluate_allocations
    assert run([('a', 30, 20), ('b', 70, 71)]) == {
        'consumers': [('a', True, 20, 10), ('b', False, 0, 70)],
        'allocated': 100, 'unallocated': 0, 'used': 20}
    # request equal to allocation accepted; rejected requests consume zero and
    # keep their full allocation as remainder; unused pool reported
    assert run([('a', 10, 10), ('b', 0, 0), ('c', 20, 21)]) == {
        'consumers': [('a', True, 10, 0), ('b', True, 0, 0), ('c', False, 0, 20)],
        'allocated': 30, 'unallocated': 70, 'used': 10}
    # pool of exactly 100 accepted; 101 refused
    assert run([('a', 100, 0)])['allocated'] == 100
    _raises(ValueError, 'pool overallocated', run, [('a', 51, 0), ('b', 50, 0)])
    # duplicate check precedes the pool check
    _raises(ValueError, 'duplicate consumer', run, [('a', 60, 0), ('a', 60, 0)])
    # boundary accepts
    assert run([('a' * 24, 0, 1000000)])['consumers'] == [('a' * 24, False, 0, 0)]
    assert len(run([('c%02d' % i, 0, 0) for i in range(32)])['consumers']) == 32
    # seeded random oracle (pool kept within 100 by construction)
    rng = random.Random(621)
    for _ in range(200):
        n = rng.randint(1, 32)
        ids = rng.sample(['t%02d' % i for i in range(40)], n)
        rows = [(t, rng.randint(0, 100 // n), rng.randint(0, 50)) for t in ids]
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
    for slot, low, high in ((1, 0, 100), (2, 0, 1000000)):
        row = ['ok', 0, 0]
        for bad in (None, True, False, 1.0, '1', [], {}):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
        for bad in (low - 1, high + 1, 10 ** 1000):
            row[slot] = bad
            _raises(ValueError, 'integer outside declared range', run, [tuple(row)])
    _raises(ValueError, 'duplicate consumer', run, [OK, ('ok', 0, 0)])


def _mix(m):
    run = m.evaluate_allocations
    # non-adjacent duplicates and non-adjacent invalid rows
    _raises(ValueError, 'duplicate consumer', run, [('a', 0, 0), ('b', 0, 0), ('c', 0, 0), ('a', 0, 0)])
    _raises(ValueError, 'integer outside declared range', run, [('a', 0, 0), ('b', 0, 0), ('c', -1, 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('a', 0, 0), ('b', 'x', 0), ('c', 0, 0)])
    # mixed-validity: subclass and bad values in later rows after valid earlier rows
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 0, 0), ('ok3', I(1), 0)])
    _raises(TypeError, 'exact tuple row required', run, [OK, ('ok2', 0, 0), T(('ok3', 0, 0))])
    _raises(TypeError, 'exact string label required', run, [('a', 0, 0), ('b', 0, 0), (S('c'), 0, 0)])
    _raises(ValueError, 'integer outside declared range', run, [('a', 0, 0), ('b', 101, 0), ('c', 0, 0)])
    # non-adjacent-order witness: reversed input produces sorted output
    rows = [('r%d' % i, 0, 0) for i in reversed(range(8))]
    assert [c[0] for c in run(rows)['consumers']] == ['r%d' % i for i in range(8)]
    # validation of every row precedes the duplicate check
    _raises(ValueError, 'integer outside declared range', run, [('ok', -1, 0), ('ok', 0, 0)])


def _late(m):
    run = m.evaluate_allocations
    _raises(TypeError, 'exact list required', run, L([OK]))
    _raises(TypeError, 'exact tuple row required', run, [T(OK)])
    _raises(TypeError, 'exact tuple row required', run, [R3('ok', 0, 0)])
    _raises(TypeError, 'exact string label required', run, [(S('ok'), 0, 0)])
    for slot in (1, 2):
        row = ['ok', 0, 0]
        for bad in (I(0), LyingGe(0), WeirdNe(0), Color.RED):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
    _raises(TypeError, 'exact list required', run, L([OK] * 33))
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', LyingGe(10 ** 30), 0)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, WeirdNe(10 ** 30))])
    assert run([tuple(('ok', int(10), int(10)))])['used'] == 10
    assert run(list([OK]))['used'] == 20


def _sym(m):
    run = m.evaluate_allocations
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
    ('_integer(allocation, 0, 100)', '_integer(allocation, -1, 100)'),
    ('_integer(allocation, 0, 100)', '_integer(allocation, 0, 101)'),
    ('_integer(request, 0, 1000000)', '_integer(request, 0, 1000001)'),
    ('        _integer(allocation, 0, 100)', '        pass'),
    ('if allocated>100', 'if allocated>=100'),
    ('if allocated>100', 'if allocated>101'),
    ('accepted=request<=allocation', 'accepted=request<allocation'),
    ('used=request if accepted else 0', 'used=request'),
    ('(consumer,accepted,used,allocation-used)', '(consumer,accepted,used,allocation-request)'),
    ("'unallocated':100-allocated", "'unallocated':allocated"),
    ("'used':sum(x[2] for x in consumers)", "'used':sum(x[3] for x in consumers)"),
    ('allocated=sum(x[1] for x in rows)', 'allocated=sum(x[1] for x in rows)+1'),
    ('for consumer,allocation,request in sorted(rows)', 'for consumer,allocation,request in rows'),
    ('if len({x[0] for x in rows})!=len(rows)', 'if False'),
    ("raise ValueError('pool overallocated')", "pass"),
    ('exact string label required', 'exact str label required'),
    ('row count must be 1..32', 'row count must be 1xx32'),
    ('duplicate consumer', 'duplicate  consumer'),
    ('pool overallocated', 'pool over-allocated'),
    ("raise ValueError('integer outside declared range')", "raise ValueError('integer outside declared bounds')"),
    ('LABEL.fullmatch(value) is None', 'LABEL.fullmatch(value) is not None'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
