import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import saga_compensation as mod

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
    assert mod.SCOPE == 'PARTIAL: compensation planning for a supplied saga, no services called'
    assert len(mod.NOT_CLAIMED) >= 4 and 'retries' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(steps, fail):
    """Independent: replay the saga with a stack of finished steps."""
    stack = []
    for i, (n, u) in enumerate(steps):
        if fail == i:
            comp, stuck = [], []
            while stack:
                n2, u2 = stack.pop()
                (comp if u2 else stuck).append(n2)
            return {'status': 'stuck' if stuck else 'compensated', 'done': None, 'failed': n, 'compensated': comp, 'stuck': stuck, '_i': i}
        stack.append((n, u))
    return {'status': 'completed', 'done': [n for n, _ in steps], 'failed': None, 'compensated': [], 'stuck': []}


def _core(m):
    S = [('reserve', True), ('charge', True), ('ship', False), ('email', True)]
    assert m.run_saga(S) == {'status': 'completed', 'done': ['reserve', 'charge', 'ship', 'email'], 'failed': None, 'compensated': [], 'stuck': []}
    assert m.run_saga(S, None) == m.run_saga(S)
    assert m.run_saga(S, 0) == {'status': 'compensated', 'done': [], 'failed': 'reserve', 'compensated': [], 'stuck': []}
    assert m.run_saga(S, 1) == {'status': 'compensated', 'done': ['reserve'], 'failed': 'charge', 'compensated': ['reserve'], 'stuck': []}
    assert m.run_saga(S, 2) == {'status': 'compensated', 'done': ['reserve', 'charge'], 'failed': 'ship', 'compensated': ['charge', 'reserve'], 'stuck': []}
    assert m.run_saga(S, 3) == {'status': 'stuck', 'done': ['reserve', 'charge', 'ship'], 'failed': 'email', 'compensated': ['charge', 'reserve'], 'stuck': ['ship']}
    # the failing step's own flag does not matter; stuck steps do not stop compensation of earlier ones
    assert m.run_saga([('a', True), ('b', False)], 1)['status'] == 'compensated'
    r = m.run_saga([('a', True), ('b', False), ('c', True), ('d', False), ('e', True)], 4)
    assert r == {'status': 'stuck', 'done': ['a', 'b', 'c', 'd'], 'failed': 'e', 'compensated': ['c', 'a'], 'stuck': ['d', 'b']}
    r = m.run_saga([('a', False), ('b', False), ('c', False)], 2)
    assert r == {'status': 'stuck', 'done': ['a', 'b'], 'failed': 'c', 'compensated': [], 'stuck': ['b', 'a']}
    assert m.run_saga([['a', True]])['done'] == ['a'] and m.run_saga((('a', True),), 0)['failed'] == 'a'
    big = [('s%d' % i, i % 2 == 0) for i in range(10)]
    assert m.run_saga(big)['done'] == ['s%d' % i for i in range(10)]
    assert m.run_saga(big, 9)['stuck'] == ['s7', 's5', 's3', 's1'] and m.run_saga(big, 9)['compensated'] == ['s8', 's6', 's4', 's2', 's0']
    assert m.run_saga([('n' * 16, True)])['done'] == ['n' * 16]
    for fail in [None] + list(range(10)):
        o = _oracle(big, fail)
        got = m.run_saga(big, fail)
        if fail is None:
            assert got == o
        else:
            assert got['failed'] == o['failed'] and got['compensated'] == o['compensated'] and got['stuck'] == o['stuck'] and got['status'] == o['status']
            assert got['done'] == [n for n, _ in big[:fail]]
    rng = random.Random(650)
    for _ in range(300):
        n = rng.randint(1, 10)
        st = [('x%d' % i, rng.random() < .6) for i in range(n)]
        f = rng.choice([None] + list(range(n)))
        got, o = m.run_saga(st, f), _oracle(st, f)
        for k in ('status', 'failed', 'compensated', 'stuck'):
            assert got[k] == o[k], (st, f)
        assert got['done'] == ([n_ for n_, _ in st] if f is None else [n_ for n_, _ in st[:f]])


def _late(m):
    ST = 'steps must be a list or tuple'
    SZ = 'steps must contain 1 to 10 entries'
    FA = 'fail_at must be None or a nonbool integer index of a step'
    PR = 'each step must be a (name, undoable) pair'
    NM = 'step names must be strings of 1 to 16 characters'
    DN = 'duplicate step name'
    UD = 'undoable must be a bool'
    ok = ('a', True)
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, ST, m.run_saga, bad)
    _raises(TypeError, ST, m.run_saga, L([ok] * 11))
    _raises(ValueError, SZ, m.run_saga, [])
    _raises(ValueError, SZ, m.run_saga, [ok] * 11)
    assert m.run_saga([('p%d' % i, True) for i in range(10)])['status'] == 'completed'
    for bad in (-1, 1, True, False, 1.0, '0', I(0), LyingI(0), LyingI(10 ** 30), I(10 ** 30), [0], 10 ** 30):
        _raises(ValueError, FA, m.run_saga, [ok], bad)
    assert m.run_saga([ok, ('b', True)], 1)['failed'] == 'b'
    _raises(ValueError, FA, m.run_saga, [ok, ('b', True)], 2)
    for K in (L, T):
        for bad in (K(ok), K(('a',))):
            _raises(ValueError, PR, m.run_saga, [bad])
            _raises(ValueError, PR, m.run_saga, [ok, bad])
    for bad in ('ab', None, 5, ('a',), ('a', True, 1), ()):
        _raises(ValueError, PR, m.run_saga, [bad])
        _raises(ValueError, PR, m.run_saga, [ok, bad])
    for bad in ('', 'x' * 17, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, NM, m.run_saga, [(bad, True)])
        _raises(ValueError, NM, m.run_saga, [ok, (bad, True)])
    _raises(ValueError, DN, m.run_saga, [ok, ('a', False)])
    _raises(ValueError, DN, m.run_saga, [ok, ('b', True), ('a', True)])
    for bad in (1, 0, None, 'True', I(1), [True], (True,), 1.0):
        _raises(ValueError, UD, m.run_saga, [('b', bad)])
        _raises(ValueError, UD, m.run_saga, [ok, ('b', bad)])
    # order: type, size, fail_at, then per step: shape, name, duplicate, flag
    _raises(TypeError, ST, m.run_saga, L([1]), I(1))
    _raises(ValueError, SZ, m.run_saga, [], I(1))
    _raises(ValueError, FA, m.run_saga, [1], I(1))
    _raises(ValueError, PR, m.run_saga, [1], 0)
    _raises(ValueError, NM, m.run_saga, [(5, 5)])
    _raises(ValueError, DN, m.run_saga, [ok, ('a', 5)])
    _raises(ValueError, UD, m.run_saga, [('b', 5), (5, True)])


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
    def __hash__(self): return hash('b')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return True
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("type(steps) not in (list, tuple)", "not isinstance(steps, (list, tuple))"),
    ("not 1 <= len(steps) <= MAX_STEPS", "not 0 <= len(steps) <= MAX_STEPS"),
    ("not 1 <= len(steps) <= MAX_STEPS", "not 1 <= len(steps) < MAX_STEPS"),
    ("MAX_STEPS = 10", "MAX_STEPS = 11"),
    ("fail_at=None", "fail_at=0"),
    ("fail_at is not None and", "True and"),
    ("type(fail_at) is not int or not 0 <= fail_at < len(steps)", "not isinstance(fail_at, int) or not 0 <= fail_at < len(steps)"),
    ("type(fail_at) is not int or not 0 <= fail_at < len(steps)", "isinstance(fail_at, bool) or not isinstance(fail_at, int) or not 0 <= fail_at < len(steps)"),
    ("not 0 <= fail_at < len(steps)", "not 0 < fail_at < len(steps)"),
    ("not 0 <= fail_at < len(steps)", "not 0 <= fail_at <= len(steps)"),
    ("type(s) not in (list, tuple) or len(s) != 2", "not isinstance(s, (list, tuple)) or len(s) != 2"),
    ("or len(s) != 2", "or len(s) > 2"),
    ("or len(s) != 2", "or len(s) < 2"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "not isinstance(name, str) or not 1 <= len(name) <= 16"),
    ("not 1 <= len(name) <= 16", "not 0 <= len(name) <= 16"),
    ("not 1 <= len(name) <= 16", "not 1 <= len(name) < 16"),
    ("not 1 <= len(name) <= 16", "not 1 <= len(name) <= 17"),
    ("if name in seen:", "if False:"),
    ("type(undoable) is not bool", "not isinstance(undoable, (bool, int))"),
    ("done = steps[:fail_at]", "done = steps[:fail_at + 1]"),
    ("done = steps[:fail_at]", "done = steps[1:fail_at]"),
    ("compensated = [s[0] for s in reversed(done) if s[1]]", "compensated = [s[0] for s in done if s[1]]"),
    ("compensated = [s[0] for s in reversed(done) if s[1]]", "compensated = [s[0] for s in reversed(done)]"),
    ("stuck = [s[0] for s in reversed(done) if not s[1]]", "stuck = [s[0] for s in done if not s[1]]"),
    ("'stuck' if stuck else 'compensated'", "'compensated' if stuck else 'stuck'"),
    ("'failed': steps[fail_at][0]", "'failed': steps[fail_at - 1][0]"),
    ("'status': 'completed'", "'status': 'compensated'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
