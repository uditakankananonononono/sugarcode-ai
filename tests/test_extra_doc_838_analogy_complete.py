import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import analogy_complete as mod

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
    assert mod.SCOPE == 'PARTIAL: completes a supplied pair by a shift or scale rule, no reasoning is performed'
    assert len(mod.NOT_CLAIMED) == 5 and 'learner insight' in mod.NOT_CLAIMED and 'real analogical reasoning' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Analogical Reasoning - Reasons by analogy' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(ps, c):
    """Independent: brute-force every candidate shift and factor instead of deriving them from the first pair."""
    shifts = [d for d in range(-100, 101) if all(a + d == b for a, b in ps)]
    scales = [k for k in range(0, 101) if all(a > 0 and a * k == b for a, b in ps)]
    sa = c + shifts[0] if shifts and c + shifts[0] >= 0 else None
    ka = c * scales[0] if scales else None
    if shifts and scales:
        return {'rule': 'both', 'answer': sa if sa == ka else None}
    if shifts:
        return {'rule': 'shift', 'answer': sa}
    if scales:
        return {'rule': 'scale', 'answer': ka}
    return {'rule': 'none', 'answer': None}


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
    f = m.analogy_complete
    assert f([(3, 5)], 10) == {'rule': 'shift', 'answer': 12}
    assert f([(3, 6)], 10) == {'rule': 'both', 'answer': None}
    assert f([(2, 4)], 2) == {'rule': 'both', 'answer': 4}
    assert f([(3, 9)], 4) == {'rule': 'both', 'answer': None}
    assert f([(1, 3), (2, 6)], 4) == {'rule': 'scale', 'answer': 12}
    assert f([(5, 2)], 10) == {'rule': 'shift', 'answer': 7}
    assert f([(5, 2)], 2) == {'rule': 'shift', 'answer': None}
    assert f([(5, 2)], 3) == {'rule': 'shift', 'answer': 0}
    assert f([(0, 0)], 7) == {'rule': 'shift', 'answer': 7}
    assert f([(0, 5)], 7) == {'rule': 'shift', 'answer': 12}
    assert f([(1, 0)], 5) == {'rule': 'both', 'answer': None}
    assert f([(4, 0)], 5) == {'rule': 'both', 'answer': None}
    assert f([(4, 0), (6, 0)], 5) == {'rule': 'scale', 'answer': 0}
    assert f([(1, 3), (2, 4), (9, 11)], 5) == {'rule': 'shift', 'answer': 7}
    assert f([(1, 2), (2, 4), (3, 6)], 5) == {'rule': 'scale', 'answer': 10}
    assert f([(1, 2), (2, 3), (3, 7)], 5) == {'rule': 'none', 'answer': None}
    assert f([(2, 4), (3, 5)], 1) == {'rule': 'shift', 'answer': 3}
    assert f([(2, 4), (3, 6)], 1) == {'rule': 'scale', 'answer': 2}
    assert f([(2, 5), (4, 10)], 3) == {'rule': 'none', 'answer': None}
    assert f([(0, 0), (1, 1)], 5) == {'rule': 'shift', 'answer': 5}
    assert f([(5, 5)], 9) == {'rule': 'both', 'answer': 9}
    assert f([(5, 5), (0, 0)], 9) == {'rule': 'shift', 'answer': 9}
    assert f([(2, 3)], 100) == {'rule': 'shift', 'answer': 101}
    assert f([(1, 100)], 100) == {'rule': 'both', 'answer': None}
    assert f([(7, 3), (8, 4)], 4) == {'rule': 'shift', 'answer': 0}
    assert f([(7, 3), (8, 4)], 3) == {'rule': 'shift', 'answer': None}
    assert f(((2, 4), [3, 6], (1, 2), (5, 10)), 6) == {'rule': 'scale', 'answer': 12}
    assert f(([1, 2],), 5)['rule'] == 'both'
    rng = random.Random(838)
    for _ in range(1500):
        n = rng.randint(1, 4)
        mode = rng.randint(0, 2)
        ps = []
        if mode == 0:
            ps = [(rng.randint(0, 100), rng.randint(0, 100)) for _ in range(n)]
        elif mode == 1:
            d = rng.randint(-20, 20)
            while len(ps) < n:
                a = rng.randint(0, 100)
                if 0 <= a + d <= 100:
                    ps.append((a, a + d))
        else:
            k = rng.randint(0, 5)
            ps = [(a, a * k) for a in (rng.randint(1, 20) for _ in range(n))]
        c = rng.randint(0, 100)
        ps = [rng.choice((list, tuple))(p) for p in ps]
        assert f(ps, c) == _oracle(ps, c), (ps, c)


def _late(m):
    f = m.analogy_complete
    PT = 'pairs must be a list or tuple'
    PS = 'pairs must contain 1 to 4 entries'
    PE = 'each pair must be an (a, b) tuple'
    AA = 'a must be a nonbool integer between 0 and 100'
    BB = 'b must be a nonbool integer between 0 and 100'
    CC = 'c must be a nonbool integer between 0 and 100'
    badint = (-1, 101, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30))
    ok = [(1, 2)]
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, PT, f, bad, 1)
    _raises(ValueError, PS, f, [], 1)
    _raises(ValueError, PS, f, [(1, 2)] * 5, 1)
    f([(1, 2)] * 4, 1)
    for bad in ('ab', None, 5, (1,), (1, 2, 3), (), {1: 2}, L([1, 2]), T((1, 2))):
        _raises(ValueError, PE, f, [bad], 1)
        _raises(ValueError, PE, f, [(1, 2), bad], 1)
    for bad in badint:
        _raises(ValueError, AA, f, [(bad, 2)], 1)
        _raises(ValueError, AA, f, [(1, 2), (bad, 2)], 1)
        _raises(ValueError, BB, f, [(1, bad)], 1)
        _raises(ValueError, BB, f, [(1, 2), (1, bad)], 1)
        _raises(ValueError, CC, f, ok, bad)
    f([(0, 100)], 0)
    f([(100, 0)], 100)
    _raises(TypeError, PT, f, None, None)
    _raises(ValueError, PS, f, [], None)
    _raises(ValueError, PE, f, [1], None)
    _raises(ValueError, AA, f, [(-1, -1)], None)
    _raises(ValueError, BB, f, [(1, -1)], None)
    _raises(ValueError, CC, f, ok, -1)


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("type(x) is int and 0 <= x <= 100", "isinstance(x, int) and 0 <= x <= 100"),
    ("type(x) is int and 0 <= x <= 100", "isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 100"),
    ("type(x) is int and 0 <= x <= 100", "type(x) is int and 1 <= x <= 100"),
    ("type(x) is int and 0 <= x <= 100", "type(x) is int and -1 <= x <= 100"),
    ("type(x) is int and 0 <= x <= 100", "type(x) is int and 0 <= x < 100"),
    ("type(x) is int and 0 <= x <= 100", "type(x) is int and 0 <= x <= 101"),
    ("type(pairs) not in (list, tuple)", "not isinstance(pairs, (list, tuple))"),
    ("not 1 <= len(pairs) <= 4", "not 0 <= len(pairs) <= 4"),
    ("not 1 <= len(pairs) <= 4", "not 1 <= len(pairs) < 4"),
    ("not 1 <= len(pairs) <= 4", "not 1 <= len(pairs) <= 5"),
    ("type(p) not in (list, tuple) or len(p) != 2", "not isinstance(p, (list, tuple)) or len(p) != 2"),
    ("type(p) not in (list, tuple) or len(p) != 2", "type(p) not in (list, tuple) or len(p) > 2"),
    ("type(p) not in (list, tuple) or len(p) != 2", "type(p) not in (list, tuple) or len(p) < 2"),
    ("diffs = {b - a for a, b in rows}", "diffs = {b - a for a, b in rows[:1]}"),
    ("diffs = {b - a for a, b in rows}", "diffs = {a - b for a, b in rows}"),
    ("shift = len(diffs) == 1", "shift = len(diffs) <= 2"),
    ("a > 0 and b % a == 0 for a, b in rows", "a > 0 and b % a == 0 for a, b in rows[:1]"),
    ("a > 0 and b % a == 0 for a, b in rows", "a >= 0 and b % (a or 1) == 0 for a, b in rows"),
    ("a > 0 and b % a == 0 for a, b in rows", "a > 0 for a, b in rows"),
    ("len({b // a for a, b in rows}) == 1", "len({b // a for a, b in rows}) <= 2"),
    ("len({b // a for a, b in rows}) == 1", "len({b // a for a, b in rows[:1]}) == 1"),
    ("s_ans = c + diffs.pop() if shift else None", "s_ans = c - diffs.pop() if shift else None"),
    ("s_ans = c + diffs.pop() if shift else None", "s_ans = c if shift else None"),
    ("if s_ans is not None and s_ans < 0:", "if s_ans is not None and s_ans < -1:"),
    ("if s_ans is not None and s_ans < 0:", "if s_ans is not None and s_ans <= 0:"),
    ("if s_ans is not None and s_ans < 0:", "if False:"),
    ("k_ans = c * (rows[0][1] // rows[0][0]) if scale else None", "k_ans = c + (rows[0][1] // rows[0][0]) if scale else None"),
    ("k_ans = c * (rows[0][1] // rows[0][0]) if scale else None", "k_ans = c * (rows[-1][1] // rows[-1][0]) + 1 if scale else None"),
    ("if shift and scale:", "if shift or scale:"),
    ("'answer': s_ans if s_ans == k_ans else None", "'answer': s_ans"),
    ("'answer': s_ans if s_ans == k_ans else None", "'answer': k_ans"),
    ("'answer': s_ans if s_ans == k_ans else None", "'answer': s_ans if s_ans == k_ans else s_ans"),
    ("return {'rule': 'shift', 'answer': s_ans}", "return {'rule': 'shift', 'answer': k_ans}"),
    ("return {'rule': 'scale', 'answer': k_ans}", "return {'rule': 'scale', 'answer': s_ans}"),
    ("return {'rule': 'none', 'answer': None}", "return {'rule': 'none', 'answer': c}"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
