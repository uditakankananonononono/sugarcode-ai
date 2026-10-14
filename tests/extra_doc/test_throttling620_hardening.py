"""Row620 hardening: exact-type subclass pins, full-message pins, behavior
oracle, non-adjacent-order and mixed-validity witnesses, boundary accepts,
mutation sweep. Tests-only delta.

Note: the 24-char label cap is doubly guarded (len check plus regex
quantifier on the same line), so single-site mutations of either half are
equivalent mutants; the refusal itself is pinned by the 'a'*25 battery case.
The initial-token count is clamped by the bucket cap before first use, so
raising it (10 -> 11) is an equivalent mutant; lowering it (10 -> 9) is in
MUTANTS and killed by the cost-10-at-time-0 witness.
"""
import enum
import pathlib
import random
import signal
import types
from collections import namedtuple

import pytest

from sugarcode.extra_doc import throttling620 as mod

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
OK = ('ok', 0, 7)


def _oracle(rows):
    ordered = sorted(rows, key=lambda r: (r[1], r[0]))
    tokens, prev, trace = 10, 0, []
    for req, ts, cost in ordered:
        tokens = min(10, tokens + 2 * (ts - prev))
        ok = cost <= tokens
        if ok:
            tokens -= cost
        trace.append((req, ts, ok, tokens))
        prev = ts
    return {'requests': trace, 'remaining_tokens': tokens,
            'accepted_count': sum(1 for t in trace if t[2])}


def _core(m):
    run = m.simulate_token_bucket
    assert run([('a', 0, 7), ('b', 0, 4), ('c', 1, 5)]) == {
        'requests': [('a', 0, True, 3), ('b', 0, False, 3), ('c', 1, True, 0)],
        'remaining_tokens': 0, 'accepted_count': 2}
    # refill cap, rejected requests consume nothing, refill happens for rejected too
    assert run([('a', 0, 10), ('b', 1, 3), ('c', 1, 2), ('d', 2, 2), ('e', 100, 10)]) == {
        'requests': [('a', 0, True, 0), ('b', 1, False, 2), ('c', 1, True, 0),
                     ('d', 2, True, 0), ('e', 100, True, 0)],
        'remaining_tokens': 0, 'accepted_count': 4}
    # cost exactly equal to tokens is accepted
    assert run([('a', 0, 10)])['requests'] == [('a', 0, True, 0)]
    # boundary accepts
    assert run([('a' * 24, 1000000, 1)])['remaining_tokens'] == 9
    assert len(run([('r%02d' % i, 0, 1) for i in range(32)])['requests']) == 32
    # seeded random oracle
    rng = random.Random(620)
    for _ in range(200):
        n = rng.randint(1, 32)
        ids = rng.sample(['t%02d' % i for i in range(40)], n)
        rows = [(t, rng.randint(0, 50), rng.randint(1, 10)) for t in ids]
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
    for slot, low, high in ((1, 0, 1000000), (2, 1, 10)):
        row = ['ok', 0, 1]
        for bad in (None, True, False, 1.0, '1', [], {}):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
        for bad in (low - 1, high + 1, 10 ** 1000):
            row[slot] = bad
            _raises(ValueError, 'integer outside declared range', run, [tuple(row)])
    _raises(ValueError, 'duplicate request', run, [OK, ('ok', 1, 1)])


def _mix(m):
    run = m.simulate_token_bucket
    # non-adjacent duplicates and non-adjacent invalid rows
    _raises(ValueError, 'duplicate request', run, [('a', 0, 1), ('b', 0, 1), ('c', 0, 1), ('a', 0, 1)])
    _raises(ValueError, 'integer outside declared range', run, [('a', 0, 1), ('b', 0, 1), ('c', -1, 1)])
    _raises(TypeError, 'exact nonbool integer required', run, [('a', 0, 1), ('b', 'x', 1), ('c', 0, 1)])
    # mixed-validity: subclass and bad values in later rows after valid earlier rows
    _raises(TypeError, 'exact nonbool integer required', run, [OK, ('ok2', 0, 1), ('ok3', I(1), 1)])
    _raises(TypeError, 'exact tuple row required', run, [OK, ('ok2', 0, 1), T(('ok3', 0, 1))])
    _raises(TypeError, 'exact string label required', run, [('a', 0, 1), ('b', 0, 1), (S('c'), 0, 1)])
    _raises(ValueError, 'integer outside declared range', run, [('a', 0, 1), ('b', 0, 11), ('c', 0, 1)])
    # non-adjacent-order witness: reversed and interleaved input produce sorted output
    rows = [('r%d' % i, (7 - i) * 3, 1) for i in range(8)]
    assert [t[0] for t in run(rows)['requests']] == ['r%d' % i for i in reversed(range(8))]
    # validation of every row precedes the duplicate check
    _raises(ValueError, 'integer outside declared range', run, [('ok', -1, 1), ('ok', 0, 1)])



def _late(m):
    run = m.simulate_token_bucket
    _raises(TypeError, 'exact list required', run, L([OK]))
    _raises(TypeError, 'exact tuple row required', run, [T(OK)])
    _raises(TypeError, 'exact tuple row required', run, [R3('ok', 0, 1)])
    _raises(TypeError, 'exact string label required', run, [(S('ok'), 0, 1)])
    for slot, good in ((1, 0), (2, 1)):
        row = ['ok', 0, 1]
        for bad in (I(good), LyingGe(good), WeirdNe(good), Color.RED):
            row[slot] = bad
            _raises(TypeError, 'exact nonbool integer required', run, [tuple(row)])
    _raises(TypeError, 'exact list required', run, L([OK] * 33))
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', LyingGe(10 ** 30), 1)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, WeirdNe(10 ** 30))])
    assert run([tuple(('ok', int(0), int(10)))])['remaining_tokens'] == 0
    assert run(list([OK]))['accepted_count'] == 1


def _sym(m):
    run = m.simulate_token_bucket
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 1)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', 0, I(1))])
    _raises(TypeError, 'exact tuple row required', run, [T(OK), OK])
    _raises(TypeError, 'exact tuple row required', run, [OK, T(OK)])
    _raises(TypeError, 'exact nonbool integer required', run, [('ok', I(1), 1), OK])
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
    ('_integer(timestamp, 0, 1000000)', '_integer(timestamp, -1, 1000000)'),
    ('_integer(timestamp, 0, 1000000)', '_integer(timestamp, 0, 1000001)'),
    ('_integer(cost, 1, 10)', '_integer(cost, 1, 11)'),
    ('_integer(cost, 1, 10)', '_integer(cost, 0, 10)'),
    ('        _integer(timestamp, 0, 1000000)', '        pass'),
    ('key=lambda x:(x[1],x[0])', 'key=lambda x:(x[1],)'),
    ('sorted(rows,key=lambda x:(x[1],x[0]))', 'sorted(rows)'),
    ('tokens=10', 'tokens=9'),
    ('tokens=min(10,tokens+2*(timestamp-previous))', 'tokens=tokens+2*(timestamp-previous)'),
    ('tokens=min(10,tokens+2*(timestamp-previous))', 'tokens=min(10,tokens+3*(timestamp-previous))'),
    ('tokens=min(10,tokens+2*(timestamp-previous))', 'tokens=min(11,tokens+2*(timestamp-previous))'),
    ('accepted=cost<=tokens', 'accepted=cost<tokens'),
    ('tokens-=cost', 'tokens-=1'),
    ('trace.append((request,timestamp,accepted,tokens))', 'trace.append((request,timestamp,accepted,0))'),
    ('previous=timestamp', 'previous=0'),
    ("'remaining_tokens':tokens", "'remaining_tokens':0"),
    ("'accepted_count':sum(x[2] for x in trace)", "'accepted_count':sum(not x[2] for x in trace)"),
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
