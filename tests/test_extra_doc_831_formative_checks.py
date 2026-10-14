import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import formative_checks as mod

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


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __ne__(self, o): return False
    def __eq__(self, o): return True
    __hash__ = int.__hash__


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('web')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: latest-score status per topic of supplied checks, no learner is assessed'
    assert len(mod.NOT_CLAIMED) == 5 and 'test quality' in mod.NOT_CLAIMED and 'grading fairness' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Formative Assessment - Assesses for learning' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(cs, pm):
    order = []
    for t, _ in cs:
        if t not in order:
            order.append(t)
    topics = []
    for t in order:
        sc = [s for tt, s in cs if tt == t]
        topics.append((t, len(sc), sc[-1], 'on_track' if sc[-1] >= pm else 'reteach'))
    rt = [x[0] for x in topics if x[3] == 'reteach']
    return {'topics': topics, 'reteach': rt, 'all_on_track': rt == []}


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def _core(m):
    f = m.formative_checks
    assert f([]) == {'topics': [], 'reteach': [], 'all_on_track': True}
    assert f([('a', 3)]) == {'topics': [('a', 1, 3, 'on_track')], 'reteach': [], 'all_on_track': True}
    assert f([('a', 2)]) == {'topics': [('a', 1, 2, 'reteach')], 'reteach': ['a'], 'all_on_track': False}
    assert f([('a', 0), ('a', 5)])['topics'] == [('a', 2, 5, 'on_track')]
    assert f([('a', 5), ('a', 0)])['topics'] == [('a', 2, 0, 'reteach')]
    r = f([('b', 1), ('a', 4), ('b', 3), ('c', 2)])
    assert r == {'topics': [('b', 2, 3, 'on_track'), ('a', 1, 4, 'on_track'), ('c', 1, 2, 'reteach')], 'reteach': ['c'], 'all_on_track': False}
    r = f([('z', 0), ('y', 0), ('z', 1)])
    assert r['reteach'] == ['z', 'y']
    assert f((['a', 5], ('b', 5)))['all_on_track'] is True
    assert f([('x' * 12, 5)])['topics'][0][0] == 'x' * 12
    # default pass_mark 3: 2 fails, 3 passes; pass_mark 1/2/4/5 differ
    assert f([('a', 3)], 4)['reteach'] == ['a'] and f([('a', 3)], 3)['reteach'] == [] and f([('a', 3)], 2)['reteach'] == []
    assert f([('a', 2)], 2)['reteach'] == [] and f([('a', 2)], 3) == f([('a', 2)])
    assert f([('a', 0)], 1)['reteach'] == ['a'] and f([('a', 1)], 1)['reteach'] == []
    assert f([('a', 4)], 5)['reteach'] == ['a'] and f([('a', 5)], 5)['reteach'] == []
    # default max_checks 8
    c8 = [('t%d' % i, 5) for i in range(8)]
    f(c8)
    _raises(ValueError, 'checks must contain at most max_checks entries', f, c8 + [('t8', 5)])
    assert len(f(c8 + [('t8', 5)], 3, 9)['topics']) == 9
    assert len(f([('t%d' % i, 5) for i in range(20)], 3, 20)['topics']) == 20
    _raises(ValueError, 'checks must contain at most max_checks entries', f, c8[:3], 3, 2)
    f(c8[:2], 3, 2)
    rng = random.Random(831)
    for _ in range(600):
        cs = [(rng.choice('abcd'), rng.randint(0, 5)) for _ in range(rng.randint(0, 8))]
        pm = rng.randint(1, 5)
        assert f(cs, pm) == _oracle(cs, pm), (cs, pm)
        assert f(cs) == _oracle(cs, 3)


def _late(m):
    f = m.formative_checks
    PM = 'pass_mark must be a nonbool integer between 1 and 5'
    MC = 'max_checks must be a nonbool integer between 1 and 20'
    CT = 'checks must be a list or tuple'
    CS = 'checks must contain at most max_checks entries'
    CP = 'each check must be a (topic, score) pair'
    TP = 'each topic must be a string of 1 to 12 characters'
    SC = 'score must be a nonbool integer between 0 and 5'
    ok = [('a', 1)]
    for bad in (0, 6, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, PM, f, [], bad)
    f([], 1)
    f([], 5)
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MC, f, [], 3, bad)
    f([], 3, 1)
    f([], 3, 20)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, CT, f, bad)
    for bad in ('ab', None, 5, ('a',), ('a', 1, 1), (), {'a': 1}, L(['a', 1]), T(('a', 1))):
        _raises(ValueError, CP, f, [bad])
        _raises(ValueError, CP, f, [('a', 1), bad])
    for bad in ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a']):
        _raises(ValueError, TP, f, [(bad, 1)])
        _raises(ValueError, TP, f, [('a', 1), (bad, 1)])
    for bad in (-1, 6, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, SC, f, [('a', bad)])
        _raises(ValueError, SC, f, [('a', 1), ('a', bad)])
    f([('a', 0)])
    f([('a', 5)])
    _raises(ValueError, PM, f, None, I(1), I(1))
    _raises(ValueError, MC, f, None, 3, I(1))
    _raises(TypeError, CT, f, None)
    _raises(ValueError, CS, f, [1] * 9)
    _raises(ValueError, CP, f, [1])
    _raises(ValueError, TP, f, [(1, -1)])
    _raises(ValueError, SC, f, [('a', -1)])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("pass_mark=3", "pass_mark=4"),
    ("pass_mark=3", "pass_mark=2"),
    ("max_checks=8", "max_checks=9"),
    ("max_checks=8", "max_checks=7"),
    ("type(pass_mark) is not int or not 1 <= pass_mark <= 5", "not isinstance(pass_mark, int) or not 1 <= pass_mark <= 5"),
    ("type(pass_mark) is not int or not 1 <= pass_mark <= 5", "isinstance(pass_mark, bool) or not isinstance(pass_mark, int) or not 1 <= pass_mark <= 5"),
    ("not 1 <= pass_mark <= 5", "not 0 <= pass_mark <= 5"),
    ("not 1 <= pass_mark <= 5", "not 1 <= pass_mark < 5"),
    ("not 1 <= pass_mark <= 5", "not 1 <= pass_mark <= 6"),
    ("type(max_checks) is not int or not 1 <= max_checks <= 20", "not isinstance(max_checks, int) or not 1 <= max_checks <= 20"),
    ("type(max_checks) is not int or not 1 <= max_checks <= 20", "isinstance(max_checks, bool) or not isinstance(max_checks, int) or not 1 <= max_checks <= 20"),
    ("not 1 <= max_checks <= 20", "not 0 <= max_checks <= 20"),
    ("not 1 <= max_checks <= 20", "not 1 <= max_checks < 20"),
    ("not 1 <= max_checks <= 20", "not 1 <= max_checks <= 21"),
    ("type(checks) not in (list, tuple)", "not isinstance(checks, (list, tuple))"),
    ("len(checks) > max_checks", "len(checks) >= max_checks"),
    ("type(c) not in (list, tuple) or len(c) != 2", "not isinstance(c, (list, tuple)) or len(c) != 2"),
    ("type(c) not in (list, tuple) or len(c) != 2", "type(c) not in (list, tuple) or len(c) > 2"),
    ("type(c) not in (list, tuple) or len(c) != 2", "type(c) not in (list, tuple) or len(c) < 2"),
    ("type(topic) is not str or not 1 <= len(topic) <= 12", "not isinstance(topic, str) or not 1 <= len(topic) <= 12"),
    ("type(topic) is not str or not 1 <= len(topic) <= 12", "type(topic) is not str or not 0 <= len(topic) <= 12"),
    ("type(topic) is not str or not 1 <= len(topic) <= 12", "type(topic) is not str or not 1 <= len(topic) < 12"),
    ("type(topic) is not str or not 1 <= len(topic) <= 12", "type(topic) is not str or not 1 <= len(topic) <= 13"),
    ("type(score) is not int or not 0 <= score <= 5", "not isinstance(score, int) or not 0 <= score <= 5"),
    ("type(score) is not int or not 0 <= score <= 5", "isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 5"),
    ("not 0 <= score <= 5", "not 1 <= score <= 5"),
    ("not 0 <= score <= 5", "not -1 <= score <= 5"),
    ("not 0 <= score <= 5", "not 0 <= score < 5"),
    ("not 0 <= score <= 5", "not 0 <= score <= 6"),
    ("state[topic] = (n + 1, score)", "state[topic] = (n + 1, max(score, state.get(topic, (0, 0))[1]))"),
    ("state[topic] = (n + 1, score)", "state[topic] = (1, score)"),
    ("state[topic] = (n + 1, score)", "state.setdefault(topic, (n + 1, score))"),
    ("'reteach' if last < pass_mark else 'on_track'", "'reteach' if last <= pass_mark else 'on_track'"),
    ("'reteach' if last < pass_mark else 'on_track'", "'reteach' if last > pass_mark else 'on_track'"),
    ("t[3] == 'reteach'", "t[3] == 'on_track'"),
    ("'all_on_track': not redo", "'all_on_track': len(redo) <= 1"),
    ("for name, (n, last) in state.items():", "for name, (n, last) in sorted(state.items()):"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
