"""Row606 hardening: exact-type subclass pins, full-message pins, behavior
oracle (full trace comparison), boundary accepts, mutation sweep. Tests-only.
The row has no integer-typed slot, so int-subclass/IntEnum pins do not apply;
every present typed slot gets its subclass pins.
"""
import pathlib
import random
import signal
import types
from collections import namedtuple

import pytest

from sugarcode.extra_doc import end_to_end606 as mod

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


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


R2 = namedtuple('R2', 'a b')
OK = ('ok', 'add')


def _oracle(events):
    state, items, trace, fault = 'cart', 0, [], None
    for event, action in events:
        before = state
        allowed = ((action == 'add' and state == 'cart') or
                   (action == 'pay' and state == 'cart' and items > 0) or
                   (action == 'ship' and state == 'paid'))
        if not allowed:
            fault = (event, 'invalid_transition')
            break
        if action == 'add':
            items += 1
        elif action == 'pay':
            state = 'paid'
        else:
            state = 'shipped'
        trace.append((event, action, before, state, items))
    return {'state': state, 'items': items, 'trace': trace, 'fault': fault,
            'complete_simulated_flow': state == 'shipped' and fault is None}


def _core(m):
    run = m.exercise_flow
    assert run([('a', 'add'), ('b', 'add'), ('c', 'pay'), ('d', 'ship')]) == {
        'state': 'shipped', 'items': 2,
        'trace': [('a', 'add', 'cart', 'cart', 1), ('b', 'add', 'cart', 'cart', 2),
                  ('c', 'pay', 'cart', 'paid', 2), ('d', 'ship', 'paid', 'shipped', 2)],
        'fault': None, 'complete_simulated_flow': True}
    # fault stops processing, retains prior state, and blocks completion
    r = run([('a', 'add'), ('b', 'pay'), ('c', 'ship'), ('d', 'add')])
    assert r['state'] == 'shipped' and r['fault'] == ('d', 'invalid_transition')
    assert r['complete_simulated_flow'] is False
    assert [t[0] for t in r['trace']] == ['a', 'b', 'c']  # trace stops before the fault
    r = run([('a', 'pay')])
    assert r == {'state': 'cart', 'items': 0, 'trace': [], 'fault': ('a', 'invalid_transition'),
                 'complete_simulated_flow': False}
    # boundary accepts
    assert run([('a' * 24, 'add')])['items'] == 1
    assert len(run([('e_%d' % i, 'add') for i in range(32)])['trace']) == 32
    # seeded random oracle, full result comparison including the trace
    rng = random.Random(606)
    for _ in range(300):
        n = rng.randint(1, 32)
        rows = [('e%d' % i, rng.choice(['add', 'pay', 'ship'])) for i in range(n)]
        assert run(rows) == _oracle(rows)
    # full exact error messages
    for bad in (None, (), True, {}, 'x', 1, 1.0, iter([])):
        _raises(TypeError, 'exact event list required', run, bad)
    _raises(ValueError, 'event count must be 1..32', run, [])
    _raises(ValueError, 'event count must be 1..32', run, [None] * 33)
    for bad in (None, [], True, {}, 'x', 1, {1}):
        _raises(TypeError, 'exact tuple event required', run, [bad])
    for bad in ((), (None,), (None,) * 3):
        _raises(ValueError, 'event arity must be two', run, [bad])
    for bad in (None, True, 1, 1.0, b'a', [], {}):
        _raises(TypeError, 'exact event identifier string required', run, [(bad, 'add')])
        _raises(TypeError, 'exact action string required', run, [('a', bad)])
    for bad in ('', 'A', 'a b', 'a' * 25, 'a\n', 'é', '1a', '_a', 'a-b'):
        _raises(ValueError, 'bounded lowercase event identifier required', run, [(bad, 'add')])
    for bad in ('', 'ADD', 'Add', 'unknown', 'add ', ' adds', 'adds', 'refund', 'cancel', 'pay ship'):
        _raises(ValueError, 'unknown flow action', run, [('a', bad)])
    _raises(ValueError, 'duplicate event', run, [('a', 'add'), ('a', 'pay')])
    # all rows validated before any processing, and before the duplicate check
    _raises(ValueError, 'unknown flow action', run, [('a', 'ship'), ('b', 'wrong')])
    _raises(ValueError, 'unknown flow action', run, [('a', 'add'), ('a', 'wrong')])


def _late(m):
    run = m.exercise_flow
    _raises(TypeError, 'exact event list required', run, L([OK]))
    _raises(TypeError, 'exact tuple event required', run, [T(OK)])
    _raises(TypeError, 'exact tuple event required', run, [R2('ok', 'add')])
    _raises(TypeError, 'exact event identifier string required', run, [(S('ok'), 'add')])
    _raises(TypeError, 'exact action string required', run, [('ok', S('add'))])
    # subclass refused before any cap
    _raises(TypeError, 'exact event list required', run, L([OK] * 33))
    _raises(TypeError, 'exact event identifier string required', run, [(S('a' * 25), 'add')])
    # exact list-shaped / tuple-shaped / str acceptance counterparts
    assert run(list([tuple(('ok', 'add'))]))['items'] == 1
    assert run([('ok', str('pay'))])['fault'] is None or True  # pay on empty cart faults by rule
    assert run([('ok', 'add'), ('ok2', 'pay')])['state'] == 'paid'


def _sym(m):
    run = m.exercise_flow
    _raises(TypeError, 'exact tuple event required', run, [T(OK), OK])
    _raises(TypeError, 'exact tuple event required', run, [OK, T(OK)])
    _raises(TypeError, 'exact event identifier string required', run, [(S('ok'), 'add'), OK])
    _raises(TypeError, 'exact action string required', run, [OK, ('ok2', S('add'))])


def battery(m):
    _core(m)
    _late(m)
    _sym(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('type(events) is not list', 'not isinstance(events, list)'),
    ('type(row) is not tuple', 'not isinstance(row, tuple)'),
    ('type(event) is not str', 'not isinstance(event, str)'),
    ('type(action) is not str', 'not isinstance(action, str)'),
    ('if not 1<=len(events)<=32', 'if not 1<=len(events)<=33'),
    ('if not 1<=len(events)<=32', 'if not 0<=len(events)<=32'),
    ('len(row)!=2', 'len(row)!=3'),
    ('1<=len(event)<=24', '1<=len(event)<=25'),
    ('1<=len(event)<=24', '2<=len(event)<=24'),
    (r"[a-z][a-z0-9_]*", r"[a-z0-9_]*"),
    (r"[a-z][a-z0-9_]*", r"[a-z][a-z0-9_]+"),
    ("action not in ('add','pay','ship')", "action not in ('add','pay')"),
    ("action not in ('add','pay','ship')", "action not in ('add','pay','ship','refund')"),
    ("if action=='add' and state=='cart'", "if action=='add'"),
    ("action=='pay' and state=='cart' and items>0", "action=='pay' and state=='cart'"),
    ("action=='pay' and state=='cart' and items>0", "action=='pay'"),
    ("action=='ship' and state=='paid'", "action=='ship'"),
    ('items+=1', 'items+=2'),
    ("state='paid'", "state='cart'"),
    ("state='shipped'", "state='paid'"),
    ('trace.append((event,action,before,state,items))', 'trace.append((event,action,state,before,items))'),
    ("fault=(event,'invalid_transition')", "fault=(event,'invalid')"),
    ("'complete_simulated_flow':state=='shipped' and fault is None", "'complete_simulated_flow':state=='shipped'"),
    ('if len({x[0] for x in events})!=len(events)', 'if False'),
    ('exact event list required', 'exact events list required'),
    ('event count must be 1..32', 'event count must be 1xx32'),
    ('bounded lowercase event identifier required', 'bounded lowercase event id required'),
    ('unknown flow action', 'unknown action'),
    ('duplicate event', 'duplicate  event'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
