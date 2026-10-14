import datetime
import itertools
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import job_queuing as mod

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


def _tick_oracle(jobs, workers):
    free, started, out = [0] * workers, set(), []
    t = 0
    while len(started) < len(jobs):
        for w in range(workers):
            if free[w] > t:
                continue
            ready = [i for i in range(len(jobs)) if i not in started and jobs[i][1] <= t]
            if not ready:
                break
            i = sorted(ready, key=lambda k: (jobs[k][2], jobs[k][1], k))[0]
            started.add(i)
            free[w] = t + jobs[i][3]
            out.append({'job': jobs[i][0], 'worker': w, 'start': t, 'end': t + jobs[i][3], 'wait': t - jobs[i][1]})
        t += 1
    return {'runs': out, 'makespan': max([r['end'] for r in out], default=0)}


def _core(m):
    assert m.run_queue([], 2) == {'runs': [], 'makespan': 0}
    jobs = [('low', 0, 5, 3), ('hi', 0, 1, 2), ('late', 1, 0, 4)]
    r = m.run_queue(jobs, 1)
    assert [(x['job'], x['start'], x['end'], x['wait']) for x in r['runs']] == [('hi', 0, 2, 0), ('late', 2, 6, 1), ('low', 6, 9, 6)]
    assert r['makespan'] == 9
    r = m.run_queue([('a', 10, 0, 1)], 2)
    assert r['runs'] == [{'job': 'a', 'worker': 0, 'start': 10, 'end': 11, 'wait': 0}]
    # equal priority: earlier arrival first, then input order
    r = m.run_queue([('x', 2, 3, 1), ('y', 1, 3, 1), ('z', 1, 3, 1)], 1)
    assert [x['job'] for x in r['runs']] == ['y', 'z', 'x']
    # lowest-index idle worker is chosen, not the one that has been idle longest
    r = m.run_queue([('p', 0, 0, 5), ('q', 0, 0, 3), ('r', 10, 0, 1)], 2)
    assert [(x['job'], x['worker']) for x in r['runs']] == [('p', 0), ('q', 1), ('r', 0)]
    rng = random.Random(644)
    for _ in range(300):
        jobs = [('j%d' % i, rng.randint(0, 30), rng.randint(0, 9), rng.randint(1, 8)) for i in range(rng.randint(0, 12))]
        w = rng.randint(1, 4)
        assert m.run_queue(jobs, w) == _tick_oracle(jobs, w)
        assert m.run_queue(tuple(jobs), w) == _tick_oracle(jobs, w)
    big = [('j%d' % i, 100, 9, 20) for i in range(20)]
    assert m.run_queue(big, 1) == _tick_oracle(big, 1) and m.run_queue(big, 1)['makespan'] == 100 + 400
    _raises(TypeError, 'jobs must be a list or tuple', m.run_queue, 'ab', 1)
    _raises(ValueError, 'jobs must contain at most 20 entries', m.run_queue, [('j%d' % i, 0, 0, 1) for i in range(21)], 1)
    for bad in (0, 5, True, 1.0):
        _raises(ValueError, 'workers must be a nonbool integer between 1 and 4', m.run_queue, [], bad)
    _raises(ValueError, 'each job must be a (name, arrival, priority, duration) tuple', m.run_queue, [('a', 0, 0)], 1)
    _raises(ValueError, 'each job must be a (name, arrival, priority, duration) tuple', m.run_queue, ['abcd'], 1)
    for bad in ('', 'x' * 17, 1):
        _raises(ValueError, 'job names must be strings of 1 to 16 characters', m.run_queue, [(bad, 0, 0, 1)], 1)
    for bad in (-1, 101, True, 1.0):
        _raises(ValueError, 'arrival must be a nonbool integer between 0 and 100', m.run_queue, [('a', bad, 0, 1)], 1)
    for bad in (-1, 10, True, 1.0):
        _raises(ValueError, 'priority must be a nonbool integer between 0 and 9', m.run_queue, [('a', 0, bad, 1)], 1)
    for bad in (0, 21, True, 1.0):
        _raises(ValueError, 'duration must be a nonbool integer between 1 and 20', m.run_queue, [('a', 0, 0, bad)], 1)
    _raises(ValueError, 'job names must be unique', m.run_queue, [('a', 0, 0, 1), ('a', 0, 0, 1)], 1)
    _raises(ValueError, 'jobs must contain at most 20 entries', m.run_queue, [None] * 21, 'zzz')



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
    _raises(TypeError, 'jobs must be a list or tuple', m.run_queue, L([('a', 0, 0, 1)]), 1)
    _raises(ValueError, 'each job must be a (name, arrival, priority, duration) tuple', m.run_queue, [T(('a', 0, 0, 1))], 1)
    _raises(ValueError, 'each job must be a (name, arrival, priority, duration) tuple', m.run_queue, [('a', 0, 0, 1), T(('b', 0, 0, 1))], 1)
    _raises(ValueError, 'job names must be strings of 1 to 16 characters', m.run_queue, [(S('a'), 0, 0, 1)], 1)
    _raises(ValueError, 'job names must be strings of 1 to 16 characters', m.run_queue, [('a', 0, 0, 1), (S('b'), 0, 0, 1)], 1)
    _raises(ValueError, 'workers must be a nonbool integer between 1 and 4', m.run_queue, [('a', 0, 0, 1)], I(2))
    _raises(ValueError, 'arrival must be a nonbool integer between 0 and 100', m.run_queue, [('a', 0, 0, 1), ('b', I(1), 0, 1)], 1)
    _raises(ValueError, 'priority must be a nonbool integer between 0 and 9', m.run_queue, [('a', 0, 0, 1), ('b', 1, I(0), 1)], 1)
    _raises(ValueError, 'duration must be a nonbool integer between 1 and 20', m.run_queue, [('a', 0, 0, 1), ('b', 1, 0, I(1))], 1)
    ok = ('a', 0, 0, 1)
    _raises(ValueError, 'each job must be a (name, arrival, priority, duration) tuple', m.run_queue, [ok, ('b', 0, 0)], 1)
    _raises(ValueError, 'job names must be strings of 1 to 16 characters', m.run_queue, [ok, ('', 0, 0, 1)], 1)
    _raises(ValueError, 'arrival must be a nonbool integer between 0 and 100', m.run_queue, [ok, ('b', 101, 0, 1)], 1)
    _raises(ValueError, 'arrival must be a nonbool integer between 0 and 100', m.run_queue, [ok, ('b', True, 0, 1)], 1)
    _raises(ValueError, 'priority must be a nonbool integer between 0 and 9', m.run_queue, [ok, ('b', 0, 10, 1)], 1)
    _raises(ValueError, 'priority must be a nonbool integer between 0 and 9', m.run_queue, [ok, ('b', 0, True, 1)], 1)
    _raises(ValueError, 'duration must be a nonbool integer between 1 and 20', m.run_queue, [ok, ('b', 0, 0, 21)], 1)
    _raises(ValueError, 'duration must be a nonbool integer between 1 and 20', m.run_queue, [ok, ('b', 0, 0, True)], 1)
    _raises(ValueError, 'job names must be unique', m.run_queue, [ok, ('b', 0, 0, 1), ('a', 0, 0, 1)], 1)


def _sym(m):
    OUT = 'jobs must be a list or tuple'
    ROW = 'each job must be a (name, arrival, priority, duration) tuple'
    for K in (L, T):
        _raises(TypeError, OUT, m.run_queue, K([('a', 0, 0, 1)]), 1)
        _raises(ValueError, ROW, m.run_queue, [K(('a', 0, 0, 1))], 1)
        _raises(ValueError, ROW, m.run_queue, [('a', 0, 0, 1), K(('a', 0, 0, 1))], 1)
        _raises(ValueError, ROW, m.run_queue, [K(('a', 0, 0, 1)), ('a', 0, 0, 1)], 1)


def battery(m):
    _core(m)
    _late(m)
    _sym(m)

MUTANTS = [
    ('type(jobs) not in (list, tuple)', 'not isinstance(jobs, (list, tuple))'),
    ('(jobs[k][2], jobs[k][1], k)', '(jobs[k][1], jobs[k][2], k)'), ('(jobs[k][2], jobs[k][1], k)', '(-jobs[k][2], jobs[k][1], k)'),
    ('(jobs[k][2], jobs[k][1], k)', '(jobs[k][2], k)'), ('(jobs[k][2], jobs[k][1], k)', '(jobs[k][2], jobs[k][1], -k)'),
    ('w = idle[0]', 'w = idle[-1]'), ('free[w] <= t', 'free[w] < t'), ('jobs[i][1] <= t]', 'jobs[i][1] < t]'),
    ("'wait': t - jobs[i][1]", "'wait': t"), ('free[w] = t + jobs[i][3]', 'free[w] = t + jobs[i][3] + 1'),
    ('[f for f in free if f > t]', '[]'), ('[jobs[i][1] for i in pending if jobs[i][1] > t]', '[]'),
    ('len(jobs) > 20', 'len(jobs) > 21'), ('_int(workers, 1, 4, ', '_int(workers, 1, 5, '), ('_int(workers, 1, 4, ', '_int(workers, 0, 4, '),
    ('_int(j[1], 0, 100, ', '_int(j[1], 0, 101, '), ('_int(j[1], 0, 100, ', '_int(j[1], 1, 100, '),
    ('_int(j[2], 0, 9, ', '_int(j[2], 0, 10, '), ('_int(j[2], 0, 9, ', '_int(j[2], 1, 9, '),
    ('_int(j[3], 1, 20, ', '_int(j[3], 1, 21, '), ('_int(j[3], 1, 20, ', '_int(j[3], 0, 20, '), ('type(v) is not int', 'isinstance(v, bool) or not isinstance(v, int)'),
    ('len({j[0] for j in jobs}) != len(jobs)', 'False'), ('len(j) != 4', 'len(j) != 5'),
    ('1 <= len(j[0]) <= 16', '1 <= len(j[0]) <= 17'), ('default=0', 'default=1'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    battery(mod)
