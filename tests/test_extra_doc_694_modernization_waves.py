import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import modernization_waves as mod

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
    assert mod.SCOPE == 'PARTIAL: topological wave ordering of supplied module dependencies, no code is analysed'
    assert len(mod.NOT_CLAIMED) == 5 and 'migration effort' in mod.NOT_CLAIMED and 'rewrite success' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(mods):
    """Independent: longest-path level per module by memoised recursion; None on cycle."""
    deps = dict(mods)
    lvl = {}

    def go(n, stack):
        if n in lvl:
            return lvl[n]
        if n in stack:
            raise RuntimeError('cycle')
        lv = 0
        for d in deps[n]:
            lv = max(lv, go(d, stack | {n}) + 1)
        lvl[n] = lv
        return lv
    try:
        for n, _ in mods:
            go(n, frozenset())
    except RuntimeError:
        return None
    top = max(lvl.values())
    waves = [[n for n, _ in mods if lvl[n] == k] for k in range(top + 1)]
    return {'waves': waves, 'order': [n for w in waves for n in w]}


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


CY = 'dependency cycle detected'


def _core(m):
    f = m.modernization_waves
    assert f([('a', [])]) == {'waves': [['a']], 'order': ['a']}
    assert f([('a', []), ('b', [])]) == {'waves': [['a', 'b']], 'order': ['a', 'b']}
    assert f([('b', ['a']), ('a', [])]) == {'waves': [['a'], ['b']], 'order': ['a', 'b']}
    r = f([('d', ['b', 'c']), ('c', ['a']), ('b', ['a']), ('a', [])])
    assert r == {'waves': [['a'], ['c', 'b'], ['d']], 'order': ['a', 'c', 'b', 'd']}
    # a module waits for its deepest dependency, not its first
    r = f([('c', ['a', 'b']), ('b', ['a']), ('a', [])], 3)
    assert r['waves'] == [['a'], ['b'], ['c']]
    r = f([('x', ['y']), ('y', []), ('z', [])], 3)
    assert r['waves'] == [['y', 'z'], ['x']]
    assert f((('b', ('a',)), ['a', ()]))['waves'] == [['a'], ['b']]
    assert f([('a', []), ('b', ['a']), ('c', ['b']), ('d', ['c']), ('e', ['d']), ('f', ['e'])])['order'] == list('abcdef')
    assert f([('a', ['b', 'c', 'd', 'e']), ('b', []), ('c', []), ('d', []), ('e', [])], 5)['waves'] == [['b', 'c', 'd', 'e'], ['a']]
    # default max_modules is 6
    ok6 = [(chr(97 + i), []) for i in range(6)]
    f(ok6)
    _raises(ValueError, 'modules must contain 1 to max_modules entries', f, ok6 + [('g', [])])
    assert len(f(ok6 + [('g', [])], 7)['order']) == 7
    assert len(f([(chr(97 + i), []) for i in range(12)], 20)['order']) == 12
    _raises(ValueError, 'modules must contain 1 to max_modules entries', f, ok6[:3], 2)
    f(ok6[:2], 2)
    _raises(ValueError, CY, f, [('a', ['b']), ('b', ['a'])])
    _raises(ValueError, CY, f, [('a', ['b']), ('b', ['c']), ('c', ['a'])])
    _raises(ValueError, CY, f, [('z', []), ('a', ['b']), ('b', ['a'])])
    rng = random.Random(694)
    for _ in range(400):
        n = rng.randint(1, 8)
        nm = [chr(97 + i) for i in range(n)]
        mods = [(nm[i], rng.sample(nm[:i], rng.randint(0, min(i, 3)))) for i in range(n)]
        if rng.random() < 0.5:
            rng.shuffle(mods)
        exp = _oracle(mods)
        assert exp is not None
        assert f(mods, 8) == exp, mods
        assert f(mods, 8)['order'] == [x for w in exp['waves'] for x in w]
    for _ in range(200):
        n = rng.randint(2, 6)
        nm = [chr(97 + i) for i in range(n)]
        mods = [(x, [d for d in rng.sample(nm, rng.randint(0, 2)) if d != x]) for x in nm]
        exp = _oracle(mods)
        if exp is None:
            _raises(ValueError, CY, f, mods, 8)
        else:
            assert f(mods, 8) == exp


def _late(m):
    f = m.modernization_waves
    MM = 'max_modules must be a nonbool integer between 1 and 20'
    MT = 'modules must be a list or tuple'
    MS = 'modules must contain 1 to max_modules entries'
    MP = 'each module must be a (name, deps) pair'
    NM = 'each name must be a string of 1 to 12 characters'
    DT = 'deps must be a list or tuple of at most 4 names'
    ND = 'names must be distinct'
    DL = 'each dependency must be a listed module'
    DS = 'a module cannot depend on itself'
    DR = 'dependencies must not repeat'
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MM, f, [('a', [])], bad)
    f([('a', [])], 1)
    f([('a', [])], 20)
    for bad in ('ab', None, 5, {}, L([('a', [])]), T([('a', [])]), L(), T()):
        _raises(TypeError, MT, f, bad)
    _raises(ValueError, MS, f, [])
    for bad in ('ab', None, 5, ('a',), ('a', [], 1), (), {'a': []}, L(['a', []]), T(('a', ()))):
        _raises(ValueError, MP, f, [bad])
        _raises(ValueError, MP, f, [('b', []), bad])
    for bad in ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a']):
        _raises(ValueError, NM, f, [(bad, [])])
        _raises(ValueError, NM, f, [('b', []), (bad, [])])
    f([('x' * 12, [])])
    for bad in ('ab', None, 5, {}, L(['b']), T(['b']), ['b'] * 5, list('bcdef')):
        _raises(ValueError, DT, f, [('a', bad)], 8)
        _raises(ValueError, DT, f, [('b', []), ('a', bad)], 8)
    _raises(ValueError, ND, f, [('a', []), ('a', [])])
    _raises(ValueError, ND, f, [('a', []), ('b', []), ('a', [])])
    for bad in ('z', '', None, 5, True, S('b'), LyingS('b'), b'b', ['b']):
        _raises(ValueError, DL, f, [('b', []), ('a', [bad])])
        _raises(ValueError, DL, f, [('b', []), ('a', ['b', bad])])
    _raises(ValueError, DS, f, [('a', ['a'])])
    _raises(ValueError, DS, f, [('b', []), ('a', ['b', 'a'])])
    _raises(ValueError, DR, f, [('b', []), ('a', ['b', 'b'])])
    # validation order
    _raises(ValueError, MM, f, None, I(1))
    _raises(TypeError, MT, f, None)
    _raises(ValueError, MS, f, [1] * 7)
    _raises(ValueError, MP, f, [1])
    _raises(ValueError, NM, f, [(1, 1)])
    _raises(ValueError, DT, f, [('a', 1), ('a', 1)])
    _raises(ValueError, ND, f, [('a', ['z']), ('a', [])])
    _raises(ValueError, DL, f, [('a', ['z', 'a'])])
    _raises(ValueError, DL, f, [('a', ['a', 'z'])][:0] or [('a', ['z'])])
    _raises(ValueError, DS, f, [('b', ['b', 'b']), ('a', [])])
    _raises(ValueError, DR, f, [('a', ['b', 'b']), ('b', ['a'])])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_modules=6", "max_modules=7"),
    ("max_modules=6", "max_modules=5"),
    ("type(max_modules) is not int or not 1 <= max_modules <= 20", "not isinstance(max_modules, int) or not 1 <= max_modules <= 20"),
    ("type(max_modules) is not int or not 1 <= max_modules <= 20", "isinstance(max_modules, bool) or not isinstance(max_modules, int) or not 1 <= max_modules <= 20"),
    ("not 1 <= max_modules <= 20", "not 0 <= max_modules <= 20"),
    ("not 1 <= max_modules <= 20", "not 1 <= max_modules < 20"),
    ("not 1 <= max_modules <= 20", "not 1 <= max_modules <= 21"),
    ("type(modules) not in (list, tuple)", "not isinstance(modules, (list, tuple))"),
    ("not 1 <= len(modules) <= max_modules", "not 0 <= len(modules) <= max_modules"),
    ("not 1 <= len(modules) <= max_modules", "not 1 <= len(modules) < max_modules"),
    ("type(mo) not in (list, tuple) or len(mo) != 2", "not isinstance(mo, (list, tuple)) or len(mo) != 2"),
    ("type(mo) not in (list, tuple) or len(mo) != 2", "type(mo) not in (list, tuple) or len(mo) > 2"),
    ("type(mo) not in (list, tuple) or len(mo) != 2", "type(mo) not in (list, tuple) or len(mo) < 2"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "not isinstance(name, str) or not 1 <= len(name) <= 12"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "type(name) is not str or not 0 <= len(name) <= 12"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "type(name) is not str or not 1 <= len(name) < 12"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "type(name) is not str or not 1 <= len(name) <= 13"),
    ("type(deps) not in (list, tuple) or len(deps) > 4", "not isinstance(deps, (list, tuple)) or len(deps) > 4"),
    ("type(deps) not in (list, tuple) or len(deps) > 4", "type(deps) not in (list, tuple) or len(deps) >= 4"),
    ("type(deps) not in (list, tuple) or len(deps) > 4", "type(deps) not in (list, tuple) or len(deps) > 5"),
    ("len(set(names)) != len(names)", "False"),
    ("type(d) is not str or d not in names", "not isinstance(d, str) or d not in names"),
    ("if d == name:", "if False:"),
    ("len(set(deps)) != len(deps)", "False"),
    ("all(d in done for d in deps)", "any(d in done for d in deps)"),
    ("all(d in done for d in deps)", "True"),
    ("if not wave:", "if wave:"),
    ("done.update(wave)", "done.update(wave[:1])"),
    ("todo = [(n, deps) for n, deps in todo if n not in done]", "todo = [(n, deps) for n, deps in todo if n in done]"),
    ("'order': [n for w in waves for n in w]", "'order': [n for w in waves for n in sorted(w, reverse=True)]"),
    ("'order': [n for w in waves for n in w]", "'order': [n for w in reversed(waves) for n in w]"),
    ("wave = [n for n, deps in todo if", "wave = [n for n, deps in reversed(todo) if"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
