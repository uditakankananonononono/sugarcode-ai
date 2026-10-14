import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import support_plan1436 as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


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
    def __hash__(self): return hash('a')



def test_scope_and_constants():
    assert mod.SCOPE == 'PARTIAL: per-step support arithmetic over supplied levels, no real teaching'
    assert mod.NOT_CLAIMED == ('real learning', 'learner readiness', 'support quality',
                               'fading over time', 'pacing', 'production readiness')
    assert 'NOT_CLAIMED' in mod.__doc__ and not (ROOT / '__init__.py').exists()
    assert (mod.MIN_STEPS, mod.MAX_STEPS, mod.MAX_LEVEL) == (1, 20, 5)


def _oracle(learner, steps):
    """Independent: explicit loops, no max()/index()."""
    support = []
    for s in steps:
        support.append(s - learner if s - learner > 0 else 0)
    peak, where = 0, None
    for i, v in enumerate(support, 1):
        if v > peak:
            peak, where = v, i
    return {'support': support, 'total': sum(support), 'peak': peak, 'peak_step': where,
            'independent': all(v == 0 for v in support)}


def test_examples():
    assert mod.plan(2, [1, 2, 3, 5, 4]) == {'support': [0, 0, 1, 3, 2], 'total': 6, 'peak': 3,
                                            'peak_step': 4, 'independent': False}
    assert mod.plan(5, [0, 5]) == {'support': [0, 0], 'total': 0, 'peak': 0, 'peak_step': None,
                                   'independent': True}
    assert mod.plan(0, [5]) == {'support': [5], 'total': 5, 'peak': 5, 'peak_step': 1, 'independent': False}
    assert mod.plan(3, (3, 3))['independent'] is True            # equal demand needs no support
    assert mod.plan(3, [4, 3])['independent'] is False
    assert mod.plan(1, [3, 2, 3])['peak_step'] == 1               # first peak wins on a tie
    assert mod.plan(1, [2, 3, 3])['peak_step'] == 2
    assert mod.plan(1, [0])['support'] == [0]                     # demand below learner is never negative
    assert mod.plan(4, [0, 1, 5])['support'] == [0, 0, 1]
    assert mod.plan(0, [0])['peak_step'] is None and mod.plan(0, [1])['peak_step'] == 1


def test_randomized_against_oracle():
    rng = random.Random(1436)
    for _ in range(500):
        learner = rng.randint(0, 5)
        steps = [rng.randint(0, 5) for _ in range(rng.randint(1, 20))]
        assert mod.plan(learner, steps) == _oracle(learner, steps)
        assert mod.plan(learner, tuple(steps)) == _oracle(learner, steps)


def test_validation_messages_boundaries_and_order():
    LRN = 'learner must be a nonbool int from 0 to 5'
    TYP = 'steps must be a list or tuple'
    SIZ = 'steps must hold 1 to 20 levels'
    LVL = 'step levels must be nonbool ints from 0 to 5'
    for bad in (-1, 6, True, False, 1.0, '1', None, I(1), 10 ** 30, -10 ** 30):
        _raises(ValueError, LRN, mod.plan, bad, [1])
    assert mod.plan(0, [1])['support'] == [1] and mod.plan(5, [1])['support'] == [0]
    for bad in (None, 'ab', 5, {}, L([1]), T([1])):
        _raises(TypeError, TYP, mod.plan, 1, bad)
    _raises(ValueError, SIZ, mod.plan, 1, [])
    _raises(ValueError, SIZ, mod.plan, 1, ())
    _raises(ValueError, SIZ, mod.plan, 1, [1] * 21)
    assert len(mod.plan(1, [1] * 20)['support']) == 20 and len(mod.plan(1, [1])['support']) == 1
    for bad in (-1, 6, True, False, 1.0, '1', None, I(1), 10 ** 30):
        _raises(ValueError, LVL, mod.plan, 1, [bad])
        _raises(ValueError, LVL, mod.plan, 1, [1, bad])
    assert mod.plan(0, [0, 5])['support'] == [0, 5]
    # order: learner, steps type, steps size, each level
    _raises(ValueError, LRN, mod.plan, 9, 'bad')
    _raises(TypeError, TYP, mod.plan, 1, L([]))
    _raises(ValueError, SIZ, mod.plan, 1, [9] * 21)
    _raises(ValueError, LVL, mod.plan, 1, [1, 9, 'x'])


def test_inputs_unchanged_and_result_fresh():
    steps = [1, 2]
    r = mod.plan(0, steps)
    r['support'].append(9)
    assert steps == [1, 2] and mod.plan(0, steps)['support'] == [1, 2]
