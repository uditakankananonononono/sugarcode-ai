import datetime
import itertools
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import dag_scheduling as mod

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


def _valid(perm, tasks):
    pos = {n: i for i, n in enumerate(perm)}
    return all(pos[d] < pos[n] for n in tasks for d in tasks[n])


def _level(n, tasks, memo):
    if n not in memo:
        memo[n] = 0 if not tasks[n] else 1 + max(_level(d, tasks, memo) for d in tasks[n])
    return memo[n]


def _check_ok(m, tasks):
    r = m.dag_schedule(tasks)
    assert _valid(r['order'], tasks) and sorted(r['order']) == sorted(tasks)
    memo = {}
    assert r['levels'] == {n: _level(n, tasks, memo) for n in r['order']}
    top = max(memo.values())
    assert r['stages'] == [sorted(n for n in tasks if memo[n] == k) for k in range(top + 1)]
    # greedy property: each pick is the smallest name whose deps are already placed
    placed = []
    for n in r['order']:
        avail = sorted(x for x in tasks if x not in placed and all(d in placed for d in tasks[x]))
        assert n == avail[0]
        placed.append(n)
    return r


def _core(m):
    t = {'deploy': ['test', 'build'], 'build': [], 'test': ['build'], 'docs': []}
    r = m.dag_schedule(t)
    assert r['order'] == ['build', 'docs', 'test', 'deploy']
    assert r['levels'] == {'build': 0, 'docs': 0, 'test': 1, 'deploy': 2}
    assert r['stages'] == [['build', 'docs'], ['test'], ['deploy']]
    assert m.dag_schedule({'a': ()}) == {'order': ['a'], 'levels': {'a': 0}, 'stages': [['a']]}
    assert m.dag_schedule({'b': [], 'a': ['b']})['order'] == ['b', 'a']
    _raises(ValueError, 'dependency graph contains a cycle', m.dag_schedule, {'a': ['a']})
    _raises(ValueError, 'dependency graph contains a cycle', m.dag_schedule, {'a': ['b'], 'b': ['a'], 'c': []})
    rng = random.Random(646)
    for _ in range(400):
        n = rng.randint(1, 6)
        names = ['t%d' % i for i in range(n)]
        tasks = {x: [d for d in names if d != x and rng.random() < 0.3] for x in names}
        if rng.random() < 0.3:
            x = rng.choice(names)
            tasks[x] = tasks[x] + [rng.choice(names)] if False else tasks[x]
        perms = [p for p in itertools.permutations(names) if _valid(p, tasks)]
        if rng.random() < 0.4 and n > 1:
            a, b = rng.sample(names, 2)
            tasks[a] = sorted(set(tasks[a]) | {b})
            tasks[b] = sorted(set(tasks[b]) | {a})
            perms = []
        else:
            perms = [p for p in itertools.permutations(names) if _valid(p, tasks)]
        if not perms:
            _raises(ValueError, 'dependency graph contains a cycle', m.dag_schedule, tasks)
        else:
            assert m.dag_schedule(tasks)['order'] == list(min(perms))
            _check_ok(m, tasks)
    for _ in range(100):
        names = ['n%02d' % i for i in range(rng.randint(1, 30))]
        tasks = {x: [d for d in names[:i] if rng.random() < 0.2] for i, x in enumerate(names)}
        _check_ok(m, tasks)
    assert len(m.dag_schedule({'n%02d' % i: [] for i in range(30)})['order']) == 30
    _raises(TypeError, 'tasks must be a dict', m.dag_schedule, [('a', [])])
    for bad in ({}, {'t%d' % i: [] for i in range(31)}):
        _raises(ValueError, 'tasks must contain between 1 and 30 entries', m.dag_schedule, bad)
    for bad in ('', 'x' * 17, 1):
        _raises(ValueError, 'task names must be strings of 1 to 16 characters', m.dag_schedule, {bad: []})
    _raises(TypeError, 'dependencies must be a list or tuple', m.dag_schedule, {'a': 'b', 'b': []})
    _raises(ValueError, 'dependencies must be unique', m.dag_schedule, {'a': ['b', 'b'], 'b': []})
    _raises(ValueError, 'dependencies must be declared tasks', m.dag_schedule, {'a': ['z']})
    _raises(ValueError, 'dependencies must be declared tasks', m.dag_schedule, {'a': [1]})
    _raises(ValueError, 'dependencies must be declared tasks', m.dag_schedule, {'a': [[1]]})
    _raises(ValueError, 'tasks must contain between 1 and 30 entries', m.dag_schedule, {'t%d' % i: 5 for i in range(31)})



class L(list):
    pass


class T(tuple):
    pass


class Dc(dict):
    pass


class S(str):
    pass


def _late(m):
    import collections
    assert m.dag_schedule({'x' * 16: []})['order'] == ['x' * 16]
    _raises(ValueError, 'task names must be strings of 1 to 16 characters', m.dag_schedule, {'x' * 17: []})
    _raises(TypeError, 'tasks must be a dict', m.dag_schedule, collections.OrderedDict({'a': []}))
    _raises(TypeError, 'tasks must be a dict', m.dag_schedule, Dc({'a': []}))
    _raises(TypeError, 'tasks must be a dict', m.dag_schedule, Dc({'a': []}))
    _raises(ValueError, 'task names must be strings of 1 to 16 characters', m.dag_schedule, {'a': [], S('b'): []})
    _raises(TypeError, 'dependencies must be a list or tuple', m.dag_schedule, {'a': [], 'b': L(['a'])})
    _raises(ValueError, 'dependencies must be declared tasks', m.dag_schedule, {'a': [], 'b': ['a', S('a')]})
    _raises(ValueError, 'task names must be strings of 1 to 16 characters', m.dag_schedule, {'a': [], 1: []})
    _raises(ValueError, 'task names must be strings of 1 to 16 characters', m.dag_schedule, {'a': [], '': []})
    _raises(TypeError, 'dependencies must be a list or tuple', m.dag_schedule, {'a': [], 'b': 'a'})
    _raises(ValueError, 'dependencies must be declared tasks', m.dag_schedule, {'a': [], 'b': ['a', 'zz']})
    _raises(ValueError, 'dependencies must be declared tasks', m.dag_schedule, {'a': [], 'b': ['a', 5]})
    _raises(ValueError, 'dependencies must be unique', m.dag_schedule, {'a': [], 'b': ['a'], 'c': ['a', 'b', 'a']})


def _sym(m):
    D = 'dependencies must be a list or tuple'
    for K in (L, T):
        _raises(TypeError, D, m.dag_schedule, {'a': K([]), 'b': []})
        _raises(TypeError, D, m.dag_schedule, {'a': [], 'b': K(['a'])})
        _raises(TypeError, D, m.dag_schedule, {'a': [], 'b': ['a'], 'c': K(['a', 'b'])})


def battery(m):
    _core(m)
    _late(m)
    _sym(m)

MUTANTS = [
    ('type(tasks) is not dict', 'not isinstance(tasks, dict)'),
    ('type(deps) not in (list, tuple)', 'not isinstance(deps, (list, tuple))'),
    ('ready = sorted(', 'ready = list('), ('n = ready[0]', 'n = ready[-1]'), ('if not d)', 'if d)'),
    ('1 + max((level[d] for d in tasks[n]), default=-1)', '1 + min((level[d] for d in tasks[n]), default=-1)'),
    ('1 + max((level[d] for d in tasks[n]), default=-1)', '1 + max((level[d] for d in tasks[n]), default=0)'),
    ('d.discard(n)', 'pass'), ('if not ready:', 'if False:'),
    ('top + 1', 'top'), ('level[n] == k', 'level[n] >= k'), ('len(set(deps)) != len(deps)', 'False'),
    ('d not in tasks', 'False'), ('1 <= len(tasks) <= 30', '1 <= len(tasks) <= 31'), ('1 <= len(tasks) <= 30', '0 <= len(tasks) <= 30'),
    ('1 <= len(name) <= 16', '1 <= len(name) <= 17'), ('1 <= len(name) <= 16', '0 <= len(name) <= 16'),
    ('type(deps) not in (list, tuple)', 'False'), ('type(d) is not str or ', ''), ('type(name) is not str or ', ''),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    battery(mod)
