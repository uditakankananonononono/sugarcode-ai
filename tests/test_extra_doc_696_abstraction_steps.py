import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import abstraction_steps as mod

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
    assert mod.SCOPE == 'PARTIAL: precondition order check over supplied step names, no change is run'
    assert len(mod.NOT_CLAIMED) == 5 and 'caller coverage' in mod.NOT_CLAIMED and 'running the change' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(steps):
    """Independent: precondition predicates over a list of accepted steps."""
    acc, vio = [], []
    pre = {
        'introduce': lambda a: True,
        'migrate': lambda a: 'introduce' in a,
        'implement': lambda a: 'introduce' in a,
        'switch': lambda a: 'migrate' in a and 'implement' in a,
        'remove': lambda a: 'switch' in a,
    }
    for i, s in enumerate(steps):
        if s not in acc and pre[s](acc):
            acc.append(s)
        else:
            vio.append((i, s))
    order = ['introduce', 'migrate', 'implement', 'switch', 'remove']
    return {'done': sorted(acc, key=order.index), 'violations': vio,
            'complete': len(acc) == 5 and vio == []}


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
    def __hash__(self): return hash('switch')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def _core(m):
    f = m.abstraction_steps
    A = ['introduce', 'migrate', 'implement', 'switch', 'remove']
    assert f([]) == {'done': [], 'violations': [], 'complete': False}
    assert f(A) == {'done': A, 'violations': [], 'complete': True}
    assert f(['introduce', 'implement', 'migrate', 'switch', 'remove'])['complete'] is True
    assert f(['introduce', 'implement', 'migrate', 'switch', 'remove'])['done'] == A
    assert f(('introduce',))['done'] == ['introduce']
    assert f(['migrate']) == {'done': [], 'violations': [(0, 'migrate')], 'complete': False}
    assert f(['implement'])['violations'] == [(0, 'implement')]
    assert f(['switch'])['violations'] == [(0, 'switch')]
    assert f(['remove'])['violations'] == [(0, 'remove')]
    assert f(['introduce', 'switch'])['violations'] == [(1, 'switch')]
    assert f(['introduce', 'migrate', 'switch'])['violations'] == [(2, 'switch')]
    assert f(['introduce', 'implement', 'switch'])['violations'] == [(2, 'switch')]
    assert f(['introduce', 'migrate', 'implement', 'remove'])['violations'] == [(3, 'remove')]
    assert f(['introduce', 'introduce'])['violations'] == [(1, 'introduce')]
    assert f(['introduce', 'migrate', 'migrate'])['violations'] == [(2, 'migrate')]
    r = f(['migrate'] + A)
    assert r['violations'] == [(0, 'migrate')] and r['done'] == A and r['complete'] is False
    # a violation does not change state: later valid steps still work
    assert f(['switch', 'introduce', 'migrate', 'implement', 'switch'])['done'] == A[:4]
    # default max_steps is 7
    f(['introduce'] * 7)
    _raises(ValueError, 'steps must contain at most max_steps entries', f, ['introduce'] * 8)
    assert f(['introduce'] * 8, 8)['violations'][-1] == (7, 'introduce')
    assert len(f(['introduce'] * 20, 20)['violations']) == 19
    _raises(ValueError, 'steps must contain at most max_steps entries', f, ['introduce'] * 3, 2)
    f(['introduce'] * 2, 2)
    import itertools
    for n in range(0, 5):
        for combo in itertools.product(A, repeat=n):
            assert f(list(combo)) == _oracle(combo), combo
    rng = random.Random(696)
    for _ in range(500):
        st = [rng.choice(A) for _ in range(rng.randint(0, 12))]
        assert f(st, 12) == _oracle(st), st
        p = A[:]
        rng.shuffle(p)
        assert f(p) == _oracle(p)


def _late(m):
    f = m.abstraction_steps
    MS = 'max_steps must be a nonbool integer between 1 and 20'
    ST = 'steps must be a list or tuple'
    SZ = 'steps must contain at most max_steps entries'
    SN = 'each step must be introduce, migrate, implement, switch or remove'
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MS, f, [], bad)
    f([], 1)
    f([], 20)
    for bad in ('ab', None, 5, {}, L(['introduce']), T(['introduce']), L(), T()):
        _raises(TypeError, ST, f, bad)
    _raises(TypeError, ST, f, L([1] * 60))
    _raises(ValueError, SZ, f, [1] * 8)
    for bad in ('', 'Introduce', 'deploy', None, 5, True, S('switch'), LyingS('switch'), b'switch', ['switch']):
        _raises(ValueError, SN, f, [bad])
        _raises(ValueError, SN, f, ['introduce', bad])
        _raises(ValueError, SN, f, ['switch', 'switch', bad])
    # validation order
    _raises(ValueError, MS, f, None, I(1))
    _raises(TypeError, ST, f, None)
    _raises(ValueError, SZ, f, [1] * 8)
    _raises(ValueError, SN, f, [1])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_steps=7", "max_steps=8"),
    ("max_steps=7", "max_steps=6"),
    ("type(max_steps) is not int or not 1 <= max_steps <= 20", "not isinstance(max_steps, int) or not 1 <= max_steps <= 20"),
    ("type(max_steps) is not int or not 1 <= max_steps <= 20", "isinstance(max_steps, bool) or not isinstance(max_steps, int) or not 1 <= max_steps <= 20"),
    ("not 1 <= max_steps <= 20", "not 0 <= max_steps <= 20"),
    ("not 1 <= max_steps <= 20", "not 1 <= max_steps < 20"),
    ("not 1 <= max_steps <= 20", "not 1 <= max_steps <= 21"),
    ("type(steps) not in (list, tuple)", "not isinstance(steps, (list, tuple))"),
    ("len(steps) > max_steps", "len(steps) >= max_steps"),
    ("type(s) is not str or s not in CANON", "not isinstance(s, str) or s not in CANON"),
    ("CANON = ('introduce', 'migrate', 'implement', 'switch', 'remove')", "CANON = ('introduce', 'implement', 'migrate', 'switch', 'remove')"),
    ("'introduce': (),", "'introduce': ('remove',),"),
    ("'migrate': ('introduce',),", "'migrate': (),"),
    ("'implement': ('introduce',),", "'implement': (),"),
    ("'switch': ('migrate', 'implement'),", "'switch': ('migrate',),"),
    ("'switch': ('migrate', 'implement'),", "'switch': ('implement',),"),
    ("'switch': ('migrate', 'implement'),", "'switch': ('introduce',),"),
    ("'remove': ('switch',),", "'remove': (),"),
    ("'remove': ('switch',),", "'remove': ('migrate',),"),
    ("if s in done or any(n not in done for n in NEEDS[s]):", "if any(n not in done for n in NEEDS[s]):"),
    ("if s in done or any(n not in done for n in NEEDS[s]):", "if s in done and any(n not in done for n in NEEDS[s]):"),
    ("if s in done or any(n not in done for n in NEEDS[s]):", "if s in done or all(n not in done for n in NEEDS[s]):"),
    ("violations.append((i, s))", "violations.append((i + 1, s))"),
    ("violations.append((i, s))\n        else:", "violations.append((i, s))\n            done.add(s)\n        else:"),
    ("len(done) == 5 and not violations", "len(done) == 5"),
    ("len(done) == 5 and not violations", "len(done) >= 4 and not violations"),
    ("len(done) == 5 and not violations", "not violations"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
