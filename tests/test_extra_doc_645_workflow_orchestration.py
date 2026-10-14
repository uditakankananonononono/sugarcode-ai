import datetime
import itertools
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import workflow_orchestration as mod

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


def _expected(steps, failing):
    out, stopped, failed = [], False, False
    for name, pol in steps:
        if stopped:
            out.append((name, 'not_run'))
        elif name in set(failing):
            out.append((name, 'failed'))
            failed = True
            stopped = pol == 'abort'
        else:
            out.append((name, 'ok'))
    overall = 'aborted' if stopped else ('completed_with_failures' if failed else 'succeeded')
    return {'statuses': out, 'overall': overall}


def _core(m):
    steps = [('build', 'abort'), ('test', 'continue'), ('lint', 'continue'), ('ship', 'abort')]
    assert m.run_workflow(steps) == {'statuses': [(n, 'ok') for n, _ in steps], 'overall': 'succeeded'}
    r = m.run_workflow(steps, ['test'])
    assert r['statuses'] == [('build', 'ok'), ('test', 'failed'), ('lint', 'ok'), ('ship', 'ok')]
    assert r['overall'] == 'completed_with_failures'
    r = m.run_workflow(steps, ['build'])
    assert r['statuses'] == [('build', 'failed'), ('test', 'not_run'), ('lint', 'not_run'), ('ship', 'not_run')]
    assert r['overall'] == 'aborted'
    assert m.run_workflow(steps, ('ship',))['overall'] == 'aborted'
    assert m.run_workflow(steps, ['test', 'ship'])['statuses'][-1] == ('ship', 'failed')
    names = ['s0', 's1', 's2', 's3', 's4']
    for pols in itertools.product(['abort', 'continue'], repeat=4):
        st = [(names[i], pols[i]) for i in range(4)]
        for k in range(5):
            for failing in itertools.combinations(names[:4], k):
                assert m.run_workflow(st, list(failing)) == _expected(st, failing)
    assert len(m.run_workflow([('s%d' % i, 'continue') for i in range(20)])['statuses']) == 20
    _raises(TypeError, 'steps must be a list or tuple', m.run_workflow, 'ab')
    for bad in ([], [('s%d' % i, 'abort') for i in range(21)]):
        _raises(ValueError, 'steps must contain between 1 and 20 entries', m.run_workflow, bad)
    _raises(ValueError, 'each step must be a (name, policy) pair', m.run_workflow, [('a',)])
    _raises(ValueError, 'each step must be a (name, policy) pair', m.run_workflow, ['ab'])
    for bad in ('', 'x' * 17, 1):
        _raises(ValueError, 'step names must be strings of 1 to 16 characters', m.run_workflow, [(bad, 'abort')])
    for bad in ('skip', 1, None):
        _raises(ValueError, 'policy must be abort or continue', m.run_workflow, [('a', bad)])
    _raises(ValueError, 'step names must be unique', m.run_workflow, [('a', 'abort'), ('a', 'abort')])
    _raises(TypeError, 'failing must be a list or tuple', m.run_workflow, [('a', 'abort')], 'a')
    for bad in (['b'], ['a', 'a'], [1]):
        _raises(ValueError, 'failing must be unique declared step names', m.run_workflow, [('a', 'abort')], bad)
    _raises(ValueError, 'steps must contain between 1 and 20 entries', m.run_workflow, [None] * 21, 'zzz')



class L(list):
    pass


class T(tuple):
    pass


class Dc(dict):
    pass


class S(str):
    pass


def _late(m):
    assert m.run_workflow([('x' * 16, 'abort')]) == {'statuses': [('x' * 16, 'ok')], 'overall': 'succeeded'}
    _raises(ValueError, 'step names must be strings of 1 to 16 characters', m.run_workflow, [('x' * 17, 'abort')])
    _raises(ValueError, 'policy must be abort or continue', m.run_workflow, [('a', S('abort'))])
    _raises(ValueError, 'failing must be unique declared step names', m.run_workflow, [('a', 'abort')], [S('a')])
    _raises(ValueError, 'step names must be strings of 1 to 16 characters', m.run_workflow, [(S('a'), 'abort')])
    _raises(TypeError, 'steps must be a list or tuple', m.run_workflow, L([('a', 'abort')]))
    _raises(TypeError, 'steps must be a list or tuple', m.run_workflow, L([('a', 'abort')]))
    _raises(ValueError, 'each step must be a (name, policy) pair', m.run_workflow, [('a', 'abort'), T(('b', 'abort'))])
    _raises(ValueError, 'step names must be strings of 1 to 16 characters', m.run_workflow, [('a', 'abort'), (S('b'), 'abort')])
    _raises(ValueError, 'policy must be abort or continue', m.run_workflow, [('a', 'abort'), ('b', S('abort'))])
    _raises(TypeError, 'failing must be a list or tuple', m.run_workflow, [('a', 'abort')], L(['a']))
    _raises(ValueError, 'failing must be unique declared step names', m.run_workflow, [('a', 'abort'), ('b', 'abort')], ['a', S('b')])
    two = [('a', 'abort'), ('b', 'continue')]
    assert m.run_workflow(two) == {'statuses': [('a', 'ok'), ('b', 'ok')], 'overall': 'succeeded'}
    assert m.run_workflow(two, ()) == m.run_workflow(two)
    ok = ('a', 'abort')
    _raises(ValueError, 'each step must be a (name, policy) pair', m.run_workflow, [ok, ('b',)])
    _raises(ValueError, 'step names must be strings of 1 to 16 characters', m.run_workflow, [ok, ('', 'abort')])
    _raises(ValueError, 'policy must be abort or continue', m.run_workflow, [ok, ('b', 'skip')])
    _raises(ValueError, 'policy must be abort or continue', m.run_workflow, [ok, ('b', 1)])
    _raises(ValueError, 'step names must be unique', m.run_workflow, [ok, ('b', 'abort'), ('a', 'continue')])
    _raises(ValueError, 'failing must be unique declared step names', m.run_workflow, [ok, ('b', 'abort')], ['a', 'zz'])
    _raises(ValueError, 'failing must be unique declared step names', m.run_workflow, [ok, ('b', 'abort')], ['a', 1])
    _raises(ValueError, 'failing must be unique declared step names', m.run_workflow, [ok, ('b', 'abort')], ['a', 'b', 'a'])


def _sym(m):
    OUT = 'steps must be a list or tuple'
    ROW = 'each step must be a (name, policy) pair'
    for K in (L, T):
        _raises(TypeError, OUT, m.run_workflow, K([('a', 'abort')]))
        _raises(ValueError, ROW, m.run_workflow, [K(('a', 'abort'))])
        _raises(ValueError, ROW, m.run_workflow, [('a', 'abort'), K(('a', 'abort'))])
        _raises(ValueError, ROW, m.run_workflow, [K(('a', 'abort')), ('a', 'abort')])
    for K in (L, T):
        _raises(TypeError, 'failing must be a list or tuple', m.run_workflow, [('a', 'abort')], K(['a']))
        _raises(TypeError, 'failing must be a list or tuple', m.run_workflow, [('a', 'abort'), ('b', 'continue')], K(['a', 'b']))


def battery(m):
    _core(m)
    _late(m)
    _sym(m)

MUTANTS = [
    ('type(steps) not in (list, tuple)', 'not isinstance(steps, (list, tuple))'),
    ('type(failing) not in (list, tuple)', 'not isinstance(failing, (list, tuple))'),
    ('failing=()', "failing=('build',)"),
    ('failing=()', "failing=('a',)"),
    ("aborted = policy == 'abort'", "aborted = policy == 'continue'"), ("aborted = policy == 'abort'", 'aborted = True'),
    ("aborted = policy == 'abort'", 'aborted = False'), ("statuses.append((name, 'not_run'))", "statuses.append((name, 'ok'))"),
    ("elif any(st == 'failed'", "elif any(st == 'ok'"), ("overall = 'aborted'", "overall = 'succeeded'"),
    ('if aborted:\n            statuses', 'if False:\n            statuses'), ('elif name in failing', 'elif name not in failing'),
    ('1 <= len(steps) <= 20', '1 <= len(steps) <= 21'), ('1 <= len(steps) <= 20', '0 <= len(steps) <= 20'),
    ("s[1] not in ('abort', 'continue')", "s[1] not in ('abort',)"), ('len(set(names)) != len(names)', 'False'),
    ('len(set(failing)) != len(failing)', 'False'), ('f not in names', 'False'), ('1 <= len(s[0]) <= 16', '1 <= len(s[0]) <= 17'),
    ('1 <= len(s[0]) <= 16', '0 <= len(s[0]) <= 16'), ('len(s) != 2', 'len(s) != 3'), ('type(failing) not in (list, tuple)', 'False'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    battery(mod)
