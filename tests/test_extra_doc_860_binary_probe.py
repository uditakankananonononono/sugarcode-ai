import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import binary_probe as mod

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
    assert mod.SCOPE == 'PARTIAL: traces binary search probes on a supplied sorted list, no thinking is assessed'
    assert len(mod.NOT_CLAIMED) == 5 and 'algorithm choice' in mod.NOT_CLAIMED and 'learner skill' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Computational Thinking - Thinks algorithmically' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(vs, t):
    """Independent: recursive search over absolute bounds, collecting probes on the way down."""
    probes = []

    def go(lo, hi):
        if lo > hi:
            return None
        m = lo + (hi - lo) // 2
        probes.append(m)
        if vs[m] == t:
            return m
        return go(m + 1, hi) if vs[m] < t else go(lo, m - 1)

    idx = go(0, len(vs) - 1)
    lin = next((i + 1 for i, v in enumerate(vs) if v == t), len(vs))
    return {'found': idx is not None, 'index': idx, 'probes': probes, 'linear_probes': lin, 'saved': lin - len(probes)}


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
    f = m.binary_probe
    assert f([5], 5) == {'found': True, 'index': 0, 'probes': [0], 'linear_probes': 1, 'saved': 0}
    assert f([5], 4) == {'found': False, 'index': None, 'probes': [0], 'linear_probes': 1, 'saved': 0}
    assert f([5], 6) == {'found': False, 'index': None, 'probes': [0], 'linear_probes': 1, 'saved': 0}
    assert f([1, 3], 3) == {'found': True, 'index': 1, 'probes': [0, 1], 'linear_probes': 2, 'saved': 0}
    assert f([1, 3], 1) == {'found': True, 'index': 0, 'probes': [0], 'linear_probes': 1, 'saved': 0}
    assert f([1, 3, 5], 1) == {'found': True, 'index': 0, 'probes': [1, 0], 'linear_probes': 1, 'saved': -1}
    vs = [2, 4, 6, 8, 10, 12, 14, 16]
    assert f(vs, 14) == {'found': True, 'index': 6, 'probes': [3, 5, 6], 'linear_probes': 7, 'saved': 4}
    assert f(vs, 2) == {'found': True, 'index': 0, 'probes': [3, 1, 0], 'linear_probes': 1, 'saved': -2}
    assert f(vs, 16) == {'found': True, 'index': 7, 'probes': [3, 5, 6, 7], 'linear_probes': 8, 'saved': 4}
    assert f(vs, 9) == {'found': False, 'index': None, 'probes': [3, 5, 4], 'linear_probes': 8, 'saved': 5}
    assert f(vs, 0) == {'found': False, 'index': None, 'probes': [3, 1, 0], 'linear_probes': 8, 'saved': 5}
    assert f(vs, 99)['probes'] == [3, 5, 6, 7]
    assert f(vs, 8)['probes'] == [3]
    # middle rounds down: 4 entries probe index 1 first, 5 entries probe index 2
    assert f([1, 2, 3, 4], 4)['probes'] == [1, 2, 3]
    assert f([1, 2, 3, 4, 5], 5)['probes'] == [2, 3, 4]
    assert f((0, 99), 99)['index'] == 1 and f([0, 99], 0)['index'] == 0
    assert f(list(range(0, 24, 2)), 22)['probes'] == [5, 8, 10, 11]
    rng = random.Random(860)
    for _ in range(1500):
        n = rng.randint(1, 12)
        vs = sorted(rng.sample(range(100), n))
        t = rng.choice(vs) if rng.random() < 0.5 else rng.randint(0, 99)
        vs = rng.choice((list, tuple))(vs)
        assert f(vs, t) == _oracle(vs, t), (vs, t)


def _late(m):
    f = m.binary_probe
    VT = 'values must be a list or tuple'
    VS = 'values must contain 1 to 12 entries'
    VE = 'each value must be a nonbool integer between 0 and 99'
    VA = 'values must be strictly ascending'
    TG = 'target must be a nonbool integer between 0 and 99'
    badint = (-1, 100, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30))
    for bad in ('ab', None, 5, {}, L([1]), T([1]), L(), T()):
        _raises(TypeError, VT, f, bad, 1)
    _raises(ValueError, VS, f, [], 1)
    _raises(ValueError, VS, f, list(range(13)), 1)
    f(list(range(12)), 1)
    for bad in badint:
        _raises(ValueError, VE, f, [bad], 1)
        _raises(ValueError, VE, f, [1, bad], 1)
        _raises(ValueError, VE, f, [1, 2, bad], 1)
        _raises(ValueError, TG, f, [1], bad)
    f([0, 99], 0)
    _raises(ValueError, VA, f, [1, 1], 1)
    _raises(ValueError, VA, f, [2, 1], 1)
    _raises(ValueError, VA, f, [1, 2, 2], 1)
    _raises(ValueError, VA, f, [1, 3, 2], 1)
    f([1, 2, 3], 1)
    # validation order
    _raises(TypeError, VT, f, None, None)
    _raises(ValueError, VS, f, [], None)
    _raises(ValueError, VE, f, [-1, -2], None)
    _raises(ValueError, VA, f, [2, 1], None)
    _raises(ValueError, TG, f, [1], -1)


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("type(x) is int and 0 <= x <= 99", "isinstance(x, int) and 0 <= x <= 99"),
    ("type(x) is int and 0 <= x <= 99", "isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 99"),
    ("type(x) is int and 0 <= x <= 99", "type(x) is int and 1 <= x <= 99"),
    ("type(x) is int and 0 <= x <= 99", "type(x) is int and -1 <= x <= 99"),
    ("type(x) is int and 0 <= x <= 99", "type(x) is int and 0 <= x < 99"),
    ("type(x) is int and 0 <= x <= 99", "type(x) is int and 0 <= x <= 100"),
    ("type(values) not in (list, tuple)", "not isinstance(values, (list, tuple))"),
    ("not 1 <= len(values) <= 12", "not 0 <= len(values) <= 12"),
    ("not 1 <= len(values) <= 12", "not 1 <= len(values) < 12"),
    ("not 1 <= len(values) <= 12", "not 1 <= len(values) <= 13"),
    ("for i in range(1, len(values)):", "for i in range(2, len(values)):"),
    ("for i in range(1, len(values)):", "for i in range(1, len(values) - 1):"),
    ("if values[i - 1] >= values[i]:", "if values[i - 1] > values[i]:"),
    ("if values[i - 1] >= values[i]:", "if values[i - 1] <= values[i]:"),
    ("low, high = 0, len(values) - 1", "low, high = 0, len(values)"),
    ("low, high = 0, len(values) - 1", "low, high = 1, len(values) - 1"),
    ("low, high = 0, len(values) - 1", "low, high = 0, len(values) - 2"),
    ("while low <= high:", "while low < high:"),
    ("mid = (low + high) // 2", "mid = (low + high + 1) // 2"),
    ("mid = (low + high) // 2", "mid = (low + high) // 1"),
    ("if values[mid] == target:", "if values[mid] >= target:"),
    ("if values[mid] < target:", "if values[mid] > target:"),
    ("low = mid + 1", "low = mid + 2"),
    ("high = mid - 1", "high = mid - 2"),
    ("index = mid\n            break", "index = mid"),
    ("linear = len(values) if index is None else index + 1", "linear = len(values) if index is None else index"),
    ("linear = len(values) if index is None else index + 1", "linear = len(values) - 1 if index is None else index + 1"),
    ("linear = len(values) if index is None else index + 1", "linear = len(values) if index is None else len(values)"),
    ("'found': index is not None", "'found': bool(index)"),
    ("'saved': linear - len(probes)", "'saved': max(0, linear - len(probes))"),
    ("'saved': linear - len(probes)", "'saved': len(probes) - linear"),
    ("'probes': probes", "'probes': sorted(probes)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
