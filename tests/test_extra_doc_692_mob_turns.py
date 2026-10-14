import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import mob_turns as mod

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
    assert mod.SCOPE == 'PARTIAL: round-robin turn plan from supplied names and minutes, no mob session runs'
    assert len(mod.NOT_CLAIMED) == 5 and 'mob quality' in mod.NOT_CLAIMED and 'real attendance' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(mem, total, tm):
    """Independent: minute-by-minute assignment, then group into turns."""
    owner = [(m // tm) for m in range(total)]
    turns = []
    for t in sorted(set(owner)):
        ms = [m for m in range(total) if owner[m] == t]
        turns.append((t, mem[t % len(mem)], ms[0], ms[-1] + 1))
    cnt = {p: 0 for p in mem}
    for t, p, s, e in turns:
        cnt[p] += e - s
    return {'turns': turns, 'minutes': [(p, cnt[p]) for p in mem]}


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
    f = m.mob_turns
    abc = ['a', 'b', 'c']
    assert f(abc, 1) == {'turns': [(0, 'a', 0, 1)], 'minutes': [('a', 1), ('b', 0), ('c', 0)]}
    assert f(abc, 10) == {'turns': [(0, 'a', 0, 10)], 'minutes': [('a', 10), ('b', 0), ('c', 0)]}
    assert f(abc, 11)['turns'] == [(0, 'a', 0, 10), (1, 'b', 10, 11)]
    assert f(abc, 25) == {'turns': [(0, 'a', 0, 10), (1, 'b', 10, 20), (2, 'c', 20, 25)], 'minutes': [('a', 10), ('b', 10), ('c', 5)]}
    r = f(abc, 45)
    assert r['turns'][3] == (3, 'a', 30, 40) and r['turns'][4] == (4, 'b', 40, 45)
    assert r['minutes'] == [('a', 20), ('b', 15), ('c', 10)]
    assert f(abc, 6, 2)['turns'] == [(0, 'a', 0, 2), (1, 'b', 2, 4), (2, 'c', 4, 6)]
    assert f(abc, 25, 10) == f(('a', 'b', 'c'), 25)
    assert f(abc, 25, 10) != f(abc, 25, 5) and f(abc, 25, 10) != f(abc, 25, 11)
    assert f(abc, 240, 30)['turns'][-1] == (7, 'b', 210, 240)
    assert len(f(abc, 240, 1)['turns']) == 240
    assert f(list('abcdefgh'), 100, 7)['turns'][8] == (8, 'a', 56, 63)
    assert f(['x' * 12, 'y', 'z'], 1)['turns'][0][1] == 'x' * 12
    rng = random.Random(692)
    for _ in range(300):
        n = rng.randint(3, 8)
        mem = [chr(97 + i) for i in range(n)]
        tot, tm = rng.randint(1, 240), rng.randint(1, 30)
        assert f(mem, tot, tm) == _oracle(mem, tot, tm), (mem, tot, tm)


def _late(m):
    f = m.mob_turns
    abc = ['a', 'b', 'c']
    MT = 'members must be a list or tuple'
    MS = 'members must contain 3 to 8 entries'
    MN = 'each name must be a string of 1 to 12 characters'
    MD = 'names must be distinct'
    TM = 'total_minutes must be a nonbool integer between 1 and 240'
    TU = 'turn_minutes must be a nonbool integer between 1 and 30'
    for bad in ('abc', None, 5, {}, L(abc), T(abc), L(), T()):
        _raises(TypeError, MT, f, bad, 1)
    for bad in ([], ['a'], ['a', 'b'], list('abcdefghi'), ['a'] * 9):
        _raises(ValueError, MS, f, bad, 1)
    f(list('abcdefgh'), 1)
    for bad in ('', 'x' * 13, None, 5, S('b'), LyingS('b'), b'b', True):
        _raises(ValueError, MN, f, [bad, 'a', 'b'], 1)
        _raises(ValueError, MN, f, ['a', 'b', bad], 1)
    f(['x' * 12, 'a', 'b'], 1)
    _raises(ValueError, MD, f, ['a', 'a', 'b'], 1)
    _raises(ValueError, MD, f, ['a', 'b', 'c', 'a'], 1)
    for bad in (0, 241, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TM, f, abc, bad)
    f(abc, 1)
    f(abc, 240)
    for bad in (0, 31, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TU, f, abc, 1, bad)
    f(abc, 1, 1)
    f(abc, 1, 30)
    _raises(TypeError, MT, f, None, I(1), I(1))
    _raises(ValueError, MS, f, ['a'], I(1), I(1))
    _raises(ValueError, MN, f, [1, 1, 1], I(1), I(1))
    _raises(ValueError, MD, f, ['a', 'a', 'b'], I(1), I(1))
    _raises(ValueError, TM, f, abc, I(1), I(1))
    _raises(ValueError, TU, f, abc, 1, I(1))


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("turn_minutes=10", "turn_minutes=11"),
    ("turn_minutes=10", "turn_minutes=9"),
    ("type(members) not in (list, tuple)", "not isinstance(members, (list, tuple))"),
    ("not 3 <= len(members) <= 8", "not 2 <= len(members) <= 8"),
    ("not 3 <= len(members) <= 8", "not 4 <= len(members) <= 8"),
    ("not 3 <= len(members) <= 8", "not 3 <= len(members) < 8"),
    ("not 3 <= len(members) <= 8", "not 3 <= len(members) <= 9"),
    ("type(p) is not str or not 1 <= len(p) <= 12", "not isinstance(p, str) or not 1 <= len(p) <= 12"),
    ("type(p) is not str or not 1 <= len(p) <= 12", "type(p) is not str or not 0 <= len(p) <= 12"),
    ("type(p) is not str or not 1 <= len(p) <= 12", "type(p) is not str or not 1 <= len(p) < 12"),
    ("type(p) is not str or not 1 <= len(p) <= 12", "type(p) is not str or not 1 <= len(p) <= 13"),
    ("len(set(members)) != len(members)", "False"),
    ("type(total_minutes) is not int or not 1 <= total_minutes <= 240", "not isinstance(total_minutes, int) or not 1 <= total_minutes <= 240"),
    ("type(total_minutes) is not int or not 1 <= total_minutes <= 240", "isinstance(total_minutes, bool) or not isinstance(total_minutes, int) or not 1 <= total_minutes <= 240"),
    ("not 1 <= total_minutes <= 240", "not 0 <= total_minutes <= 240"),
    ("not 1 <= total_minutes <= 240", "not 1 <= total_minutes < 240"),
    ("not 1 <= total_minutes <= 240", "not 1 <= total_minutes <= 241"),
    ("type(turn_minutes) is not int or not 1 <= turn_minutes <= 30", "not isinstance(turn_minutes, int) or not 1 <= turn_minutes <= 30"),
    ("type(turn_minutes) is not int or not 1 <= turn_minutes <= 30", "isinstance(turn_minutes, bool) or not isinstance(turn_minutes, int) or not 1 <= turn_minutes <= 30"),
    ("not 1 <= turn_minutes <= 30", "not 0 <= turn_minutes <= 30"),
    ("not 1 <= turn_minutes <= 30", "not 1 <= turn_minutes < 30"),
    ("not 1 <= turn_minutes <= 30", "not 1 <= turn_minutes <= 31"),
    ("while start < total_minutes:", "while start <= total_minutes:"),
    ("end = min(start + turn_minutes, total_minutes)", "end = start + turn_minutes"),
    ("end = min(start + turn_minutes, total_minutes)", "end = min(start + turn_minutes + 1, total_minutes)"),
    ("turns.append((i, members[i % n], start, end))", "turns.append((i, members[i % n], start + 1, end))"),
    ("turns.append((i, members[i % n], start, end))", "turns.append((i + 1, members[i % n], start, end))"),
    ("turns.append((i, members[i % n], start, end))", "turns.append((i, members[(i + 1) % n], start, end))"),
    ("mins[i % n] += end - start", "mins[i % n] += turn_minutes"),
    ("mins[i % n] += end - start", "mins[0] += end - start"),
    ("start = end\n        i += 1", "start = end\n        i += 2"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
