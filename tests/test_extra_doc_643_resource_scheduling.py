import datetime
import itertools
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import resource_scheduling as mod

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
    signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
    return True


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


import heapq


def _expected(jobs, machines):
    heap = [(0, i) for i in range(machines)]
    heapq.heapify(heap)
    out, loads = [], [0] * machines
    for name, d in jobs:
        load, i = heapq.heappop(heap)
        out.append({'job': name, 'machine': i, 'start': load, 'end': load + d})
        loads[i] = load + d
        heapq.heappush(heap, (load + d, i))
    return {'assignments': out, 'loads': loads, 'makespan': max(loads)}


def _core(m):
    r = m.schedule_jobs([('a', 5), ('b', 3), ('c', 4), ('d', 2)], 2)
    assert [(x['job'], x['machine'], x['start'], x['end']) for x in r['assignments']] == [
        ('a', 0, 0, 5), ('b', 1, 0, 3), ('c', 1, 3, 7), ('d', 0, 5, 7)]
    assert r['loads'] == [7, 7] and r['makespan'] == 7
    assert m.schedule_jobs([], 3) == {'assignments': [], 'loads': [0, 0, 0], 'makespan': 0}
    assert m.schedule_jobs([('a', 1), ('b', 1)], 3)['loads'] == [1, 1, 0]
    rng = random.Random(643)
    for _ in range(300):
        jobs = [('j%d' % i, rng.randint(1, 1000)) for i in range(rng.randint(0, 30))]
        k = rng.randint(1, 8)
        r = m.schedule_jobs(jobs, k)
        assert r == _expected(jobs, k)
        assert sum(r['loads']) == sum(d for _, d in jobs)
        if jobs:
            assert r['makespan'] >= max(d for _, d in jobs) and r['makespan'] * k >= sum(d for _, d in jobs)
        assert m.schedule_jobs(tuple(jobs), k) == r
    _raises(TypeError, 'jobs must be a list or tuple', m.schedule_jobs, 'ab', 1)
    _raises(ValueError, 'jobs must contain at most 30 entries', m.schedule_jobs, [('j%d' % i, 1) for i in range(31)], 1)
    for bad in (0, 9, True, 1.0):
        _raises(ValueError, 'machines must be a nonbool integer between 1 and 8', m.schedule_jobs, [], bad)
    _raises(ValueError, 'each job must be a (name, duration) pair', m.schedule_jobs, [('a',)], 1)
    _raises(ValueError, 'each job must be a (name, duration) pair', m.schedule_jobs, ['ab'], 1)
    for bad in ('', 'x' * 17, 1):
        _raises(ValueError, 'job names must be strings of 1 to 16 characters', m.schedule_jobs, [(bad, 1)], 1)
    for bad in (0, 1001, True, 1.0):
        _raises(ValueError, 'duration must be a nonbool integer between 1 and 1000', m.schedule_jobs, [('a', bad)], 1)
    _raises(ValueError, 'job names must be unique', m.schedule_jobs, [('a', 1), ('a', 2)], 1)
    _raises(ValueError, 'jobs must contain at most 30 entries', m.schedule_jobs, [None] * 31, 'zzz')



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
    _raises(TypeError, 'jobs must be a list or tuple', m.schedule_jobs, L([('a', 1)]), 1)
    _raises(ValueError, 'each job must be a (name, duration) pair', m.schedule_jobs, [('a', 1), T(('b', 1))], 1)
    _raises(ValueError, 'job names must be strings of 1 to 16 characters', m.schedule_jobs, [('a', 1), (S('b'), 1)], 1)
    _raises(ValueError, 'machines must be a nonbool integer between 1 and 8', m.schedule_jobs, [('a', 1)], I(2))
    _raises(ValueError, 'duration must be a nonbool integer between 1 and 1000', m.schedule_jobs, [('a', 1), ('b', I(2))], 2)
    ok = ('a', 1)
    _raises(ValueError, 'each job must be a (name, duration) pair', m.schedule_jobs, [ok, ('b',)], 1)
    _raises(ValueError, 'job names must be strings of 1 to 16 characters', m.schedule_jobs, [ok, ('', 1)], 1)
    _raises(ValueError, 'duration must be a nonbool integer between 1 and 1000', m.schedule_jobs, [ok, ('b', 0)], 1)
    _raises(ValueError, 'duration must be a nonbool integer between 1 and 1000', m.schedule_jobs, [ok, ('b', True)], 1)
    _raises(ValueError, 'job names must be unique', m.schedule_jobs, [ok, ('b', 1), ('a', 2)], 1)
    _raises(ValueError, 'duration must be a nonbool integer between 1 and 1000', m.schedule_jobs, [('j%d' % i, 1) for i in range(29)] + [('z', 1001)], 1)


def battery(m):
    _core(m)
    _late(m)

MUTANTS = [
    ('type(jobs) not in (list, tuple)', 'not isinstance(jobs, (list, tuple))'),
    ('key=lambda i: (loads[i], i)', 'key=lambda i: (loads[i], -i)'), ('key=lambda i: (loads[i], i)', 'key=lambda i: (i, loads[i])'),
    ('loads[k] += dur', 'loads[k] += 1'), ("'start': loads[k]", "'start': 0"), ("loads[k] + dur}", "loads[k] + dur + 1}"),
    ('max(loads)', 'min(loads)'), ('len(jobs) > 30', 'len(jobs) > 31'), ('_int(machines, 1, 8, ', '_int(machines, 1, 9, '),
    ('_int(machines, 1, 8, ', '_int(machines, 0, 8, '), ('_int(j[1], 1, 1000, ', '_int(j[1], 1, 1001, '),
    ('_int(j[1], 1, 1000, ', '_int(j[1], 0, 1000, '), ('type(v) is not int', 'isinstance(v, bool) or not isinstance(v, int)'),
    ('len({j[0] for j in jobs}) != len(jobs)', 'False'), ('1 <= len(j[0]) <= 16', '1 <= len(j[0]) <= 17'),
    ('1 <= len(j[0]) <= 16', '0 <= len(j[0]) <= 16'), ('len(j) != 2', 'len(j) != 3'), ('loads, out = [0] * machines', 'loads, out = [0] * (machines + 1)'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    battery(mod)
