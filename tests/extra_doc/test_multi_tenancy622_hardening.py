"""Row622 hardening: exact-type subclass pins, full-message pins, behavior
oracle, non-adjacent-order and mixed-validity witnesses, boundary accepts,
mutation sweep. Tests-only delta.

Note: the 24-char label cap is doubly guarded (len check plus regex
quantifier on the same line), so single-site mutations of either half are
equivalent mutants; the refusal itself is pinned by the 'a'*25 battery case.
Iterating the conflict-detection loop in sorted rather than supplied order is
an equivalent mutant: it raises the same bare message either way and the
stored dict ends identical, so no battery witness can distinguish them.
"""
import enum
import pathlib
import random
import signal
import types
from collections import namedtuple

import pytest

from sugarcode.extra_doc import multi_tenancy622 as mod

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
OK = ('ok', 'ok', 'one', 7)


def _oracle(rows):
    stored = {}
    for _, o, r, v in rows:
        k = (o, r)
        if k in stored and stored[k] != v:
            raise ValueError('conflicting record value')
        stored[k] = v
    acc = []
    for req, o, r, v in sorted(rows, key=lambda x: (x[0], x[1], x[2])):
        ok = req == o
        acc.append((req, o, r, ok, v if ok else None))
    return {'accesses': acc, 'denied_count': sum(1 for a in acc if not a[3])}


def _core(m):
    run = m.read_tenant_records
    assert run([('a', 'a', 'one', 7), ('a', 'b', 'one', 8)]) == {
        'accesses': [('a', 'a', 'one', True, 7), ('a', 'b', 'one', False, None)],
        'denied_count': 1}
    # denied exposes None, never the stored value; negative and zero values exposed when allowed
    assert run([('a', 'b', 'r', -1000000)])['accesses'] == [('a', 'b', 'r', False, None)]
    assert run([('a', 'a', 'r', -1000000)])['accesses'][0][4] == -1000000
    assert run([('a', 'a', 'r', 0)])['accesses'][0][4] == 0
    # same record value shared across requesters is fine; conflict refused in either input order
    assert run([('a', 'a', 'r', 1), ('b', 'a', 'r', 1)])['denied_count'] == 1
    _raises(ValueError, 'conflicting record value', run, [('a', 'a', 'r', 1), ('b', 'a', 'r', 2)])
    _raises(ValueError, 'conflicting record value', run, [('b', 'a', 'r', 2), ('a', 'a', 'r', 1)])
    # duplicate identity check precedes the conflict check
    _raises(ValueError, 'duplicate access request', run, [('a', 'a', 'r', 1), ('a', 'a', 'r', 2)])
    # boundary accepts
    assert run([('a' * 24, 'a' * 24, 'a' * 24, 1000000)])['denied_count'] == 0
    assert len(run([('c%02d' % i, 'o', 'r%d' % i, 0) for i in range(32)])['accesses']) == 32
    # seeded random oracle (unique triples, consistent record values by construction)
    rng = random.Random(622)
    for _ in range(200):
        n = rng.randint(1, 16)
        combos = rng.sample([(req, own, 'r%d' % j) for j in range(6) for req in 'ab' for own in 'ab'], n)
        rows = [(req, own, rec, hash((own, rec)) % 2000 - 1000) for req, own, rec in combos]
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
    for slot in (0, 1, 2):
        row = ['ok', 'ok', 'one', 7]
        for bad in (None, 1, True, 1.0, b'a', [], {}):
            row[slot] = bad
            _raises(TypeError, 'exact string label required', run, [tuple(row)])
        for bad in ('', 'A', 'a b', 'a' * 25, 'a\n', 'é', '1a', '_a', 'a-b'):
            row[slot] = bad
            _raises(ValueError, 'label must be 1..24 lowercase identifier characters', run, [tuple(row)])
    for bad in (None, True, False, 1.0, '1', [], {}):
        _raises(TypeError, 'exact nonbool integer required', run, [('ok', 'ok', 'one', bad)])
    for bad in (-1000001, 1000001, 10 ** 1000):
        _raises(ValueError, 'integer outside declared range', run, [('ok', 'ok', 'one', bad)])
    _raises(ValueError, 'duplicate access request', run, [OK, ('ok', 'ok', 'one', 8)])


def _mix(m):
    run = m.read_tenant_records
    # non-adjacent duplicates and non-adjacent invalid rows
    _raises(ValueError, 'duplicate access request',
            run, [('a', 'a', 'r', 1), ('b', 'b', 's', 1), ('c', 'c', 't', 1), ('a', 'a', 'r', 1)])
    _raises(ValueError, 'integer outside declared range',
            run, [('a', 'a', 'r', 0), ('b', 'b', 's', 0), ('c', 'c', 't', 1000001)])
    _raises(TypeError, 'exact string label required',
            run, [('a', 'a', 'r', 0), ('b', 1, 's', 0), ('c', 'c', 't', 0)])
    # mixed-validity: subclass and bad values in later rows after valid earlier rows
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 'ok2', 'r', 0), ('ok3', 'ok3', 's', I(1))])
    _raises(TypeError, 'exact tuple row required', run, [OK, ('ok2', 'ok2', 'r', 0), T(('ok3', 'ok3', 's', 0))])
    _raises(TypeError, 'exact string label required', run, [('a', 'a', 'r', 0), ('b', 'b', 's', 0), (S('c'), 'c', 't', 0)])
    # conflict rows at non-adjacent positions
    _raises(ValueError, 'conflicting record value',
            run, [('a', 'a', 'r', 1), ('b', 'b', 's', 0), ('c', 'c', 't', 0), ('d', 'a', 'r', 2)])
    # non-adjacent-order witness: reversed input produces sorted output
    rows = [('r%d' % i, 'r%d' % i, 's', 0) for i in reversed(range(8))]
    assert [a[0] for a in run(rows)['accesses']] == ['r%d' % i for i in range(8)]
    # validation of every row precedes the duplicate check
    _raises(ValueError, 'integer outside declared range', run, [('ok', 'ok', 'one', 2000000), ('ok', 'ok', 'one', 0)])


def _late(m):
    run = m.read_tenant_records
    _raises(TypeError, 'exact list required', run, L([OK]))
    _raises(TypeError, 'exact tuple row required', run, [T(OK)])
    _raises(TypeError, 'exact tuple row required', run, [R4('ok', 'ok', 'one', 7)])
    for slot in (0, 1, 2):
        row = ['ok', 'ok', 'one', 7]
        row[slot] = S('ok' if slot < 2 else 'one')
        _raises(TypeError, 'exact string label required', run, [tuple(row)])
    for bad in (I(7), LyingGe(7), WeirdNe(7), Color.RED):
        _raises(TypeError, 'exact nonbool integer required', run, [('ok', 'ok', 'one', bad)])
    _raises(TypeError, 'exact list required', run, L([OK] * 33))
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 'ok', 'one', LyingGe(10 ** 30))])
    _raises(TypeError, 'exact string label required', run, [(S('a' * 25), 'ok', 'one', 7)])
    assert run([tuple(('ok', 'ok', 'one', int(7)))])['accesses'][0][4] == 7
    assert run(list([OK]))['denied_count'] == 0


def _sym(m):
    run = m.read_tenant_records
    _raises(TypeError, 'exact tuple row required', run, [T(OK), OK])
    _raises(TypeError, 'exact tuple row required', run, [OK, T(OK)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 'ok', 'one', I(1)), OK])
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 'ok2', 'two', I(1))])
    _raises(TypeError, 'exact string label required', run, [(S('ok'), 'ok', 'one', 7), OK])
    _raises(TypeError, 'exact string label required', run, [OK, ('ok2', S('ok2'), 'two', 7)])


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
    ('_integer(value, -1000000, 1000000)', '_integer(value, -1000000, 1000001)'),
    ('_integer(value, -1000000, 1000000)', '_integer(value, -1000001, 1000000)'),
    ('        _label(owner)', '        pass'),
    ('        _label(record)', '        pass'),
    ('identities=[x[:3] for x in rows]', 'identities=[x[:2] for x in rows]'),
    ('identities=[x[:3] for x in rows]', 'identities=[x[0] for x in rows]'),
    ('allowed=requester==owner', 'allowed=requester!=owner'),
    ('value if allowed else None', 'value'),
    ('if key in stored and stored[key]!=value', 'if key in stored and stored[key]==value'),
    ('if key in stored and stored[key]!=value', 'if stored[key]!=value'),
    ("raise ValueError('conflicting record value')", "pass"),
    ('(requester,owner,record,allowed,value if allowed else None)',
     '(requester,owner,record,allowed,None)'),
    ('accesses.append((requester,owner,record,allowed,value if allowed else None))',
     'accesses.append((owner,requester,record,allowed,value if allowed else None))'),
    ("'denied_count':sum(not x[3] for x in accesses)", "'denied_count':sum(x[3] for x in accesses)"),
    ('for requester,owner,record,value in sorted(rows)', 'for requester,owner,record,value in rows'),
    ('if len(set(identities))!=len(rows)', 'if False'),
    ('exact string label required', 'exact str label required'),
    ('row count must be 1..32', 'row count must be 1xx32'),
    ('duplicate access request', 'duplicate  access request'),
    ('conflicting record value', 'conflicting record  value'),
    ("raise ValueError('integer outside declared range')", "raise ValueError('integer outside declared bounds')"),
    ('LABEL.fullmatch(value) is None', 'LABEL.fullmatch(value) is not None'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
