import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import runbook_steps as mod

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
    assert mod.SCOPE == 'PARTIAL: dependency ordering of supplied runbook steps, nothing executed'
    assert len(mod.NOT_CLAIMED) >= 4 and 'rollback' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(steps):
    """Independent: index-based simulation with explicit state flags; depth by memoized recursion."""
    n = len(steps)
    idx = {s[0]: i for i, s in enumerate(steps)}
    state = [0] * n
    order = []
    while len(order) < n:
        pick = None
        for i in range(n):
            if state[i] == 0 and all(state[idx[d]] == 1 for d in steps[i][1]):
                pick = i
                break
        if pick is None:
            return None
        state[pick] = 1
        order.append(steps[pick][0])
    memo = {}

    def dep(i):
        if i not in memo:
            memo[i] = 1 + max([dep(idx[d]) for d in steps[i][1]] or [0])
        return memo[i]
    depth = {s[0]: dep(i) for i, s in enumerate(steps)}
    return {'order': order, 'depth': depth, 'max_depth': max(depth.values())}


def _core(m):
    assert m.runbook_steps([('a', [])]) == {'order': ['a'], 'depth': {'a': 1}, 'max_depth': 1}
    r = m.runbook_steps([('deploy', ['build', 'test']), ('build', []), ('test', ['build']), ('notify', ['deploy'])])
    assert r == {'order': ['build', 'test', 'deploy', 'notify'], 'depth': {'deploy': 3, 'build': 1, 'test': 2, 'notify': 4}, 'max_depth': 4}
    assert list(r['depth']) == ['build', 'test', 'deploy', 'notify']
    # first available step in listed order wins, not the one with fewest needs or the alphabetical one
    r = m.runbook_steps([('z', []), ('a', []), ('m', ['z'])])
    assert r['order'] == ['z', 'a', 'm']
    r = m.runbook_steps([('b', ['a']), ('c', []), ('a', [])])
    assert r['order'] == ['c', 'a', 'b']
    r = m.runbook_steps([('b', ['c']), ('a', []), ('c', [])])
    assert r['order'] == ['a', 'c', 'b']
    assert m.runbook_steps(((('a', ()), ('b', ('a',)))))['order'] == ['a', 'b']
    assert m.runbook_steps([['a', ['b']], ['b', []]])['order'] == ['b', 'a']
    r = m.runbook_steps([('t', ['a', 'b', 'c', 'd']), ('a', []), ('b', ['a']), ('c', ['b']), ('d', [])])
    assert r['order'] == ['a', 'b', 'c', 'd', 't'] and r['depth']['t'] == 4 and r['max_depth'] == 4
    r = m.runbook_steps([('n%d' % i, [] if i == 0 else ['n%d' % (i - 1)]) for i in range(20)])
    assert r['max_depth'] == 20 and r['order'] == ['n%d' % i for i in range(20)]
    assert m.runbook_steps([('s' * 16, []), ('t' * 16, ['s' * 16])])['depth'] == {'s' * 16: 1, 't' * 16: 2}
    r = m.runbook_steps([('a', []), ('b', []), ('c', ['a', 'b'])])
    assert r['depth'] == {'a': 1, 'b': 1, 'c': 2}
    r = m.runbook_steps([('a', []), ('b', ['a']), ('c', ['a', 'b'])])
    assert r['depth']['c'] == 3                                     # max of needs, not the count or the first
    r = m.runbook_steps([('a', []), ('b', ['a']), ('c', ['b', 'a'])])
    assert r['depth']['c'] == 3
    rng = random.Random(639)
    for _ in range(500):
        n = rng.randint(1, 12)
        names = rng.sample(['s%d' % i for i in range(30)], n)
        steps = []
        for i, nm in enumerate(names):
            pool = names[:]
            k = min(len(pool) - 1, rng.randint(0, 4))
            steps.append((nm, rng.sample([p for p in pool if p != nm], k) if rng.random() < .8 else []))
        exp = _oracle(steps)
        if exp is None:
            _raises(ValueError, 'steps contain a cycle', m.runbook_steps, steps)
        else:
            assert m.runbook_steps(steps) == exp, steps
            assert list(m.runbook_steps(steps)['depth']) == exp['order']


def _late(m):
    ST = 'steps must be a list or tuple'
    SZ = 'steps must contain 1 to 20 entries'
    PR = 'each step must be a (name, needs) pair'
    NM = 'step names must be strings of 1 to 16 characters'
    DN = 'duplicate step name'
    NT = 'needs must be a list or tuple'
    NS = 'needs must contain at most 4 entries'
    ND = 'needs must be strings of 1 to 16 characters'
    DD = 'duplicate need'
    UN = 'unknown step in needs'
    CY = 'steps contain a cycle'
    ok = ('a', [])
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, ST, m.runbook_steps, bad)
    _raises(TypeError, ST, m.runbook_steps, L([ok] * 21))
    _raises(ValueError, SZ, m.runbook_steps, [])
    _raises(ValueError, SZ, m.runbook_steps, [ok] * 21)
    assert m.runbook_steps([('p%d' % i, []) for i in range(20)])['max_depth'] == 1
    for K in (L, T):
        for bad in (K(ok), K(('a',))):
            _raises(ValueError, PR, m.runbook_steps, [bad])
            _raises(ValueError, PR, m.runbook_steps, [ok, bad])
    for bad in ('ab', None, 5, ('a',), ('a', [], 1), ()):
        _raises(ValueError, PR, m.runbook_steps, [bad])
        _raises(ValueError, PR, m.runbook_steps, [ok, bad])
    for bad in ('', 'x' * 17, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, NM, m.runbook_steps, [(bad, [])])
        _raises(ValueError, NM, m.runbook_steps, [ok, (bad, [])])
    _raises(ValueError, DN, m.runbook_steps, [ok, ('a', [])])
    _raises(ValueError, DN, m.runbook_steps, [ok, ('b', []), ('a', [])])
    for bad in ('x', None, 5, {}, L(), T(), L(['a']), T(['a'])):
        _raises(TypeError, NT, m.runbook_steps, [('b', bad)])
        _raises(TypeError, NT, m.runbook_steps, [ok, ('b', bad)])
    _raises(ValueError, NS, m.runbook_steps, [('b', ['a', 'c', 'd', 'e', 'f'])])
    _raises(ValueError, NS, m.runbook_steps, [('b', [1, 1, 1, 1, 1])])      # size before items
    assert m.runbook_steps([ok, ('c', []), ('d', []), ('e', []), ('b', ['a', 'c', 'd', 'e'])])['depth']['b'] == 2
    for bad in ('', 'x' * 17, None, 5, S('a'), LyingS('a'), b'a', ['a']):
        _raises(ValueError, ND, m.runbook_steps, [ok, ('b', [bad])])
        _raises(ValueError, ND, m.runbook_steps, [ok, ('b', ['a', bad])])
    _raises(ValueError, DD, m.runbook_steps, [ok, ('b', ['a', 'a'])])
    _raises(ValueError, DD, m.runbook_steps, [ok, ('c', []), ('b', ['a', 'c', 'a'])])
    _raises(ValueError, UN, m.runbook_steps, [('b', ['a'])])
    _raises(ValueError, UN, m.runbook_steps, [ok, ('b', ['a', 'zz'])])
    _raises(ValueError, CY, m.runbook_steps, [('a', ['a'])])
    _raises(ValueError, CY, m.runbook_steps, [('a', ['b']), ('b', ['a'])])
    _raises(ValueError, CY, m.runbook_steps, [('c', []), ('a', ['b']), ('b', ['a'])])
    _raises(ValueError, CY, m.runbook_steps, [('a', ['c']), ('b', ['a']), ('c', ['b'])])
    # order: type, size, then per step: shape, name, duplicate, needs type, needs size, need, duplicate; then unknown, then cycle
    _raises(TypeError, ST, m.runbook_steps, L([1]))
    _raises(ValueError, SZ, m.runbook_steps, [])
    _raises(ValueError, PR, m.runbook_steps, [1, (5, 5)])
    _raises(ValueError, NM, m.runbook_steps, [(5, 'x')])
    _raises(ValueError, DN, m.runbook_steps, [ok, ('a', 'x')])               # duplicate before needs type
    _raises(TypeError, NT, m.runbook_steps, [('b', 'x' * 9)])
    _raises(TypeError, NT, m.runbook_steps, [('b', L([1] * 9))])
    _raises(ValueError, ND, m.runbook_steps, [('b', [5, 5])])
    _raises(ValueError, DD, m.runbook_steps, [('b', ['q', 'q'])])            # duplicate before unknown
    _raises(ValueError, ND, m.runbook_steps, [('b', ['q']), ('c', [5])])     # later step's need type before unknown
    _raises(ValueError, UN, m.runbook_steps, [('a', ['b', 'zz']), ('b', ['a'])])   # unknown before cycle


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


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("type(steps) not in (list, tuple)", "not isinstance(steps, (list, tuple))"),
    ("not 1 <= len(steps) <= MAX_STEPS", "not 0 <= len(steps) <= MAX_STEPS"),
    ("not 1 <= len(steps) <= MAX_STEPS", "not 1 <= len(steps) < MAX_STEPS"),
    ("MAX_STEPS = 20", "MAX_STEPS = 21"),
    ("MAX_NEEDS = 4", "MAX_NEEDS = 5"),
    ("MAX_NEEDS = 4", "MAX_NEEDS = 3"),
    ("type(s) not in (list, tuple) or len(s) != 2", "not isinstance(s, (list, tuple)) or len(s) != 2"),
    ("or len(s) != 2", "or len(s) > 2"),
    ("or len(s) != 2", "or len(s) < 2"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "not isinstance(name, str) or not 1 <= len(name) <= 16"),
    ("not 1 <= len(name) <= 16", "not 0 <= len(name) <= 16"),
    ("not 1 <= len(name) <= 16", "not 1 <= len(name) < 16"),
    ("not 1 <= len(name) <= 16", "not 1 <= len(name) <= 17"),
    ("if name in needs_of:", "if False:"),
    ("type(needs) not in (list, tuple)", "not isinstance(needs, (list, tuple))"),
    ("if len(needs) > MAX_NEEDS:", "if len(needs) >= MAX_NEEDS:"),
    ("type(n) is not str or not 1 <= len(n) <= 16", "not isinstance(n, str) or not 1 <= len(n) <= 16"),
    ("not 1 <= len(n) <= 16", "not 0 <= len(n) <= 16"),
    ("not 1 <= len(n) <= 16", "not 1 <= len(n) < 16"),
    ("not 1 <= len(n) <= 16", "not 1 <= len(n) <= 17"),
    ("if n in seen:", "if False:"),
    ("if n not in needs_of:", "if False:"),
    ("if name not in done and all(n in done for n in needs_of[name]):", "if all(n in done for n in needs_of[name]):"),
    ("if name not in done and all(n in done for n in needs_of[name]):", "if name not in done:"),
    ("all(n in done for n in needs_of[name])", "any(n in done for n in needs_of[name])"),
    ("order.append(name)", "order.insert(0, name)"),
    ("depth[name] = 1 + max((depth[n] for n in needs_of[name]), default=0)", "depth[name] = 1 + len(needs_of[name])"),
    ("depth[name] = 1 + max((depth[n] for n in needs_of[name]), default=0)", "depth[name] = 1 + min((depth[n] for n in needs_of[name]), default=0)"),
    ("depth[name] = 1 + max((depth[n] for n in needs_of[name]), default=0)", "depth[name] = max((depth[n] for n in needs_of[name]), default=0)"),
    ("'max_depth': max(depth.values())", "'max_depth': len(order)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
