import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import scaffold_fade as mod

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
    assert mod.SCOPE == 'PARTIAL: monotone fade check of supplied support levels, no learner is observed'
    assert len(mod.NOT_CLAIMED) == 5 and 'learner readiness' in mod.NOT_CLAIMED and 'pacing' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(lv):
    rises = [i for i in range(len(lv)) if i > 0 and lv[i] - lv[i - 1] > 0]
    drops = sum(max(lv[i - 1] - lv[i], 0) for i in range(1, len(lv)))
    return {'rises': rises, 'drops': drops, 'final': lv[-1], 'faded': rises == [] and lv[-1] == 0}


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def _core(m):
    f = m.scaffold_fade
    assert f([0]) == {'rises': [], 'drops': 0, 'final': 0, 'faded': True}
    assert f([3]) == {'rises': [], 'drops': 0, 'final': 3, 'faded': False}
    assert f([5, 3, 1, 0]) == {'rises': [], 'drops': 5, 'final': 0, 'faded': True}
    assert f([5, 3, 3, 0]) == {'rises': [], 'drops': 5, 'final': 0, 'faded': True}
    assert f([5, 3, 1]) == {'rises': [], 'drops': 4, 'final': 1, 'faded': False}
    assert f([0, 1]) == {'rises': [1], 'drops': 0, 'final': 1, 'faded': False}
    assert f([2, 0, 2, 0]) == {'rises': [2], 'drops': 4, 'final': 0, 'faded': False}
    assert f([1, 2, 3, 2, 1, 0]) == {'rises': [1, 2], 'drops': 3, 'final': 0, 'faded': False}
    assert f([4, 5, 4, 5, 0]) == {'rises': [1, 3], 'drops': 6, 'final': 0, 'faded': False}
    assert f((5, 0)) == {'rises': [], 'drops': 5, 'final': 0, 'faded': True}
    assert f([0, 0, 0])['faded'] is True and f([0, 0, 1])['faded'] is False
    # default max_steps 6
    f([1] * 6)
    _raises(ValueError, 'levels must contain 1 to max_steps entries', f, [1] * 7)
    assert f([1] * 7, 7)['final'] == 1
    assert f([0] * 20, 20)['faded'] is True
    _raises(ValueError, 'levels must contain 1 to max_steps entries', f, [1] * 3, 2)
    f([1] * 2, 2)
    rng = random.Random(739)
    for _ in range(600):
        lv = [rng.randint(0, 5) for _ in range(rng.randint(1, 20))]
        assert f(lv, 20) == _oracle(lv), lv
    import itertools
    for n in range(1, 6):
        for lv in itertools.product(range(0, 4), repeat=n):
            assert f(list(lv), 6) == _oracle(list(lv)), lv


def _late(m):
    f = m.scaffold_fade
    MS = 'max_steps must be a nonbool integer between 1 and 20'
    LT = 'levels must be a list or tuple'
    LS = 'levels must contain 1 to max_steps entries'
    LV = 'each level must be a nonbool integer between 0 and 5'
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MS, f, [1], bad)
    f([1], 1)
    f([1], 20)
    for bad in ('ab', None, 5, {}, L([1]), T([1]), L(), T()):
        _raises(TypeError, LT, f, bad)
    _raises(ValueError, LS, f, [])
    for bad in (-1, 6, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30), [1]):
        _raises(ValueError, LV, f, [bad])
        _raises(ValueError, LV, f, [1, bad])
        _raises(ValueError, LV, f, [1, 1, bad])
    f([0, 5])
    _raises(ValueError, MS, f, None, I(1))
    _raises(TypeError, LT, f, None)
    _raises(ValueError, LS, f, [])
    _raises(ValueError, LV, f, [-1])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_steps=6", "max_steps=7"),
    ("max_steps=6", "max_steps=5"),
    ("type(max_steps) is not int or not 1 <= max_steps <= 20", "not isinstance(max_steps, int) or not 1 <= max_steps <= 20"),
    ("type(max_steps) is not int or not 1 <= max_steps <= 20", "isinstance(max_steps, bool) or not isinstance(max_steps, int) or not 1 <= max_steps <= 20"),
    ("not 1 <= max_steps <= 20", "not 0 <= max_steps <= 20"),
    ("not 1 <= max_steps <= 20", "not 1 <= max_steps < 20"),
    ("not 1 <= max_steps <= 20", "not 1 <= max_steps <= 21"),
    ("type(levels) not in (list, tuple)", "not isinstance(levels, (list, tuple))"),
    ("not 1 <= len(levels) <= max_steps", "not 0 <= len(levels) <= max_steps"),
    ("not 1 <= len(levels) <= max_steps", "not 1 <= len(levels) < max_steps"),
    ("type(v) is not int or not 0 <= v <= 5", "not isinstance(v, int) or not 0 <= v <= 5"),
    ("type(v) is not int or not 0 <= v <= 5", "isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 5"),
    ("not 0 <= v <= 5", "not 1 <= v <= 5"),
    ("not 0 <= v <= 5", "not -1 <= v <= 5"),
    ("not 0 <= v <= 5", "not 0 <= v < 5"),
    ("not 0 <= v <= 5", "not 0 <= v <= 6"),
    ("for i in range(1, len(levels)):", "for i in range(0, len(levels)):"),
    ("for i in range(1, len(levels)):", "for i in range(1, len(levels) - 1):"),
    ("if levels[i] > levels[i - 1]:", "if levels[i] >= levels[i - 1]:"),
    ("if levels[i] > levels[i - 1]:", "if levels[i] < levels[i - 1]:"),
    ("rises.append(i)", "rises.append(i - 1)"),
    ("drops += levels[i - 1] - levels[i]", "drops += 1"),
    ("drops += levels[i - 1] - levels[i]", "drops += levels[i]"),
    ("final = levels[-1]", "final = levels[0]"),
    ("final = levels[-1]", "final = max(levels)"),
    ("'faded': not rises and final == 0", "'faded': not rises"),
    ("'faded': not rises and final == 0", "'faded': final == 0"),
    ("'faded': not rises and final == 0", "'faded': not rises and final <= 1"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
