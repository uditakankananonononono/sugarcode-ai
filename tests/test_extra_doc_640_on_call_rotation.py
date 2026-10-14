import datetime
import itertools
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import on_call_rotation as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


def _load(src):
    m = types.ModuleType('mutant')
    exec(compile(src, 'mutant', 'exec'), m.__dict__)
    return m


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


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _expected(people, days, shift, over):
    idx, used, sched = 0, 0, []
    for d in range(days):
        sched.append(people[idx])
        used += 1
        if used == shift:
            idx, used = (idx + 1) % len(people), 0
    for d, p in over.items():
        sched[d] = p
    counts = {p: sum(1 for x in sched if x == p) for p in people}
    hand = [d for d in range(1, days) if sched[d] != sched[d - 1]]
    return {'schedule': sched, 'counts': counts, 'handoffs': hand}


def _core(m):
    r = m.on_call_schedule(['ann', 'bo', 'cy'], 7, 2)
    assert r['schedule'] == ['ann', 'ann', 'bo', 'bo', 'cy', 'cy', 'ann']
    assert r['counts'] == {'ann': 3, 'bo': 2, 'cy': 2} and r['handoffs'] == [2, 4, 6]
    r = m.on_call_schedule(('a', 'b'), 4, 1, {1: 'a', 2: 'a'})
    assert r['schedule'] == ['a', 'a', 'a', 'b'] and r['handoffs'] == [3]
    assert m.on_call_schedule(['solo'], 3) == {'schedule': ['solo'] * 3, 'counts': {'solo': 3}, 'handoffs': []}
    rng = random.Random(640)
    for _ in range(300):
        people = ['p%d' % i for i in range(rng.randint(1, 10))]
        days, shift = rng.randint(1, 60), rng.randint(1, 7)
        over = {d: rng.choice(people) for d in rng.sample(range(days), rng.randint(0, min(days, 6)))}
        assert m.on_call_schedule(people, days, shift, over) == _expected(people, days, shift, over)
        assert m.on_call_schedule(tuple(people), days, shift) == _expected(people, days, shift, {})
    _raises(TypeError, 'people must be a list or tuple', m.on_call_schedule, 'ab', 1)
    for bad in ([], ['p%d' % i for i in range(11)]):
        _raises(ValueError, 'people must contain between 1 and 10 entries', m.on_call_schedule, bad, 1)
    for bad in (['a', 'a'], [''], ['x' * 17], [1], [None]):
        _raises(ValueError, 'people must be unique strings of 1 to 16 characters', m.on_call_schedule, bad, 1)
    for bad in (0, 61, True, 1.0, '1'):
        _raises(ValueError, 'days must be a nonbool integer between 1 and 60', m.on_call_schedule, ['a'], bad)
    for bad in (0, 8, True, 1.0):
        _raises(ValueError, 'shift_days must be a nonbool integer between 1 and 7', m.on_call_schedule, ['a'], 3, bad)
    _raises(TypeError, 'overrides must be a dict or None', m.on_call_schedule, ['a'], 3, 1, [1])
    for bad in (-1, 3, True, 1.0, 'x'):
        _raises(ValueError, 'override days must be nonbool integers within the schedule', m.on_call_schedule, ['a'], 3, 1, {bad: 'a'})
    for bad in ('zed', 1, None):
        _raises(ValueError, 'override people must be listed people', m.on_call_schedule, ['a'], 3, 1, {0: bad})
    assert len(m.on_call_schedule(['p%d' % i for i in range(10)], 60, 7)['schedule']) == 60
    _raises(ValueError, 'people must contain between 1 and 10 entries', m.on_call_schedule, [], 'zzz')



class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class Dc(dict):
    pass


class S(str):
    pass


def _late(m):
    _raises(TypeError, 'people must be a list or tuple', m.on_call_schedule, L(['a', 'b']), 3)
    _raises(ValueError, 'people must be unique strings of 1 to 16 characters', m.on_call_schedule, ['a', S('b')], 3)
    _raises(TypeError, 'overrides must be a dict or None', m.on_call_schedule, ['a', 'b'], 3, 1, Dc({0: 'a'}))
    _raises(ValueError, 'override people must be listed people', m.on_call_schedule, ['a', 'b'], 3, 1, {0: 'a', 1: S('b')})
    DAYS = 'days must be a nonbool integer between 1 and 60'
    SHIFT = 'shift_days must be a nonbool integer between 1 and 7'
    _raises(ValueError, DAYS, m.on_call_schedule, ['a', 'b'], I(3))
    _raises(ValueError, SHIFT, m.on_call_schedule, ['a', 'b'], 3, I(2))
    _raises(ValueError, 'override days must be nonbool integers within the schedule', m.on_call_schedule, ['a', 'b'], 3, 2, {I(2): 'a'})
    _raises(ValueError, 'override days must be nonbool integers within the schedule', m.on_call_schedule, ['a', 'b'], 3, 2, {0: 'a', I(1): 'b'})
    assert m.on_call_schedule(['a', 'b'], 3, 2, {2: 'a'})['schedule'] == ['a', 'a', 'a']
    assert m.on_call_schedule(['a', 'b'], 3)['schedule'] == ['a', 'b', 'a']
    assert m.on_call_schedule(['a', 'b', 'c'], 5) == {'schedule': ['a', 'b', 'c', 'a', 'b'], 'counts': {'a': 2, 'b': 2, 'c': 1}, 'handoffs': [1, 2, 3, 4]}
    assert m.on_call_schedule(('a', 'b'), 4, 1, None)['schedule'] == ['a', 'b', 'a', 'b']
    E = 'people must be unique strings of 1 to 16 characters'
    _raises(ValueError, E, m.on_call_schedule, ['a', 1], 3)
    _raises(ValueError, E, m.on_call_schedule, ['a', 'b', 'a'], 3)
    _raises(ValueError, E, m.on_call_schedule, ['a', 'b', ''], 3)
    _raises(ValueError, E, m.on_call_schedule, ['a', 'b', 'x' * 17], 3)
    O = 'override days must be nonbool integers within the schedule'
    _raises(ValueError, O, m.on_call_schedule, ['a'], 3, 1, {0: 'a', 3: 'a'})
    _raises(ValueError, O, m.on_call_schedule, ['a'], 3, 1, {0: 'a', 'x': 'a'})
    _raises(ValueError, 'override people must be listed people', m.on_call_schedule, ['a'], 3, 1, {0: 'a', 1: 'zed'})


def _sym(m):
    P = 'people must be a list or tuple'
    for K in (L, T):
        _raises(TypeError, P, m.on_call_schedule, K(('a', 'b')), 3)
        _raises(TypeError, P, m.on_call_schedule, K(['a']), 1, 1, None)


def battery(m):
    _core(m)
    _late(m)
    _sym(m)

MUTANTS = [
    ('type(people) not in (list, tuple)', 'not isinstance(people, (list, tuple))'),
    ('type(over) is not dict', 'not isinstance(over, dict)'),
    ('shift_days=1, overrides=None', 'shift_days=2, overrides=None'),
    ('(d // shift_days) % n', '(d * shift_days) % n'), ('(d // shift_days) % n', '(d // shift_days + 1) % n'),
    ('sched[d] != sched[d - 1]', 'sched[d] == sched[d - 1]'), ('range(1, days)', 'range(days)'),
    ('over.get(d, ', 'over.get(d + 1, '), ('counts[p] += 1', 'counts[p] += 2'),
    ('_int(days, 1, 60, ', '_int(days, 1, 61, '), ('_int(days, 1, 60, ', '_int(days, 0, 60, '),
    ('_int(shift_days, 1, 7, ', '_int(shift_days, 1, 8, '), ('_int(shift_days, 1, 7, ', '_int(shift_days, 0, 7, '),
    ('1 <= len(people) <= 10', '1 <= len(people) <= 11'), ('1 <= len(people) <= 10', '0 <= len(people) <= 10'),
    ('len(set(people)) != len(people)', 'False'), ('1 <= len(p) <= 16', '1 <= len(p) <= 17'),
    ('1 <= len(p) <= 16', '0 <= len(p) <= 16'), ('0 <= d < days', '0 <= d <= days'), ('0 <= d < days', '1 <= d < days'),
    ('p not in people', 'False'), ('type(d) is not int', 'isinstance(d, bool) or not isinstance(d, int)'), ('type(v) is not int', 'isinstance(v, bool) or not isinstance(v, int)'),
    ('type(over) is not dict', 'False'), ('type(p) is not str or ', ''),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    battery(mod)
