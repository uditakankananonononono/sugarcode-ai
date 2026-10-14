import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import diagnostic_gaps as mod

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
    assert mod.SCOPE == 'PARTIAL: ranks supplied skill tallies against a threshold, no learner is diagnosed'
    assert len(mod.NOT_CLAIMED) == 5 and 'test validity' in mod.NOT_CLAIMED and 'curriculum coverage' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Diagnostic Assessment - Identifies needs' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(its, th):
    """Independent: float-free selection sort over scaled integers (share * 20!/... avoided by lcm scaling)."""
    import math
    lcm = 1
    for _, a, _ in its:
        lcm = lcm * a // math.gcd(lcm, a)
    scaled = [(c * (lcm // a), s, c * 100 // a) for s, a, c in its]   # share * lcm
    needs = [t for t in scaled if t[0] * 100 < th * lcm]
    out = []
    while needs:
        best = needs[0]
        for t in needs[1:]:
            if (t[0], t[1]) < (best[0], best[1]):
                best = t
        out.append((best[1], best[2]))
        needs.remove(best)
    return {'needs': out, 'secure': len(its) - len(out), 'clear': not out}


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
    f = m.diagnostic_gaps
    assert f([('a', 10, 5)]) == {'needs': [], 'secure': 1, 'clear': True}
    assert f([('a', 10, 4)]) == {'needs': [('a', 40)], 'secure': 0, 'clear': False}
    assert f([('a', 3, 1)]) == {'needs': [('a', 33)], 'secure': 0, 'clear': False}
    assert f([('a', 20, 0)])['needs'] == [('a', 0)]
    # default threshold 50: 49% is a need, 50% is not, and 25 vs 26 vs 75 would differ
    assert f([('a', 100 // 5, 9)])['needs'] == [('a', 45)] and f([('a', 20, 10)])['needs'] == []
    assert f([('a', 20, 9)]) == f([('a', 20, 9)], 50)
    assert f([('a', 20, 6)])['needs'] == [('a', 30)] and f([('a', 20, 6)], 25)['needs'] == []
    assert f([('a', 20, 5)], 25)['needs'] == [] and f([('a', 20, 5)], 26)['needs'] == [('a', 25)]
    assert f([('a', 20, 20)], 100)['needs'] == [] and f([('a', 20, 19)], 100)['needs'] == [('a', 95)]
    assert f([('a', 1, 0)], 1)['needs'] == [('a', 0)] and f([('a', 1, 1)], 1)['needs'] == []
    # ordering: lowest exact share first
    r = f([('a', 10, 4), ('b', 10, 1), ('c', 10, 3)])
    assert r['needs'] == [('b', 10), ('c', 30), ('a', 40)]
    # ties on share broken by name, regardless of input order
    assert f([('z', 10, 2), ('b', 5, 1), ('m', 20, 4)])['needs'] == [('b', 20), ('m', 20), ('z', 20)]
    assert f([('m', 20, 4), ('z', 10, 2), ('b', 5, 1)])['needs'] == [('b', 20), ('m', 20), ('z', 20)]
    # same floored percent, different exact share: 7/20 = 35.0 below 6/17 = 35.29
    assert f([('a', 17, 6), ('b', 20, 7)])['needs'] == [('b', 35), ('a', 35)]
    assert f([('b', 17, 6), ('a', 20, 7)])['needs'] == [('a', 35), ('b', 35)]
    # a skill exactly at the threshold is not a need, just under it is
    assert f([('a', 3, 1), ('b', 3, 2)], 67)['needs'] == [('a', 33), ('b', 66)]
    assert f([('a', 3, 1), ('b', 3, 2)], 66)['needs'] == [('a', 33)]
    assert f([('a', 3, 1), ('b', 3, 2)])['secure'] == 1
    assert f([('x' * 12, 4, 1)])['needs'][0][0] == 'x' * 12
    assert f((['a', 4, 1], ('b', 4, 4)))['needs'] == [('a', 25)]
    assert len(f([(chr(97 + i), 4, 0) for i in range(8)])['needs']) == 8
    rng = random.Random(833)
    for _ in range(600):
        n = rng.randint(1, 8)
        its = []
        for i in range(n):
            a = rng.randint(1, 20)
            its.append((rng.choice('abcdefgh') + chr(97 + i), a, rng.randint(0, a)))
        rng.shuffle(its)
        th = rng.randint(1, 100)
        assert f(its, th) == _oracle(its, th), (its, th)
        assert f(its) == _oracle(its, 50)


def _late(m):
    f = m.diagnostic_gaps
    TH = 'threshold must be a nonbool integer between 1 and 100'
    IT = 'items must be a list or tuple'
    IS = 'items must contain 1 to 8 entries'
    IE = 'each item must be a (skill, asked, correct) tuple'
    SK = 'each skill must be an ASCII string of 1 to 12 characters'
    AS = 'asked must be a nonbool integer between 1 and 20'
    CO = 'correct must be a nonbool integer between 0 and asked'
    DS = 'skills must be distinct'
    ok = [('a', 1, 1)]
    for bad in (0, 101, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TH, f, ok, bad)
    f(ok, 1)
    f(ok, 100)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, IT, f, bad)
    _raises(ValueError, IS, f, [])
    _raises(ValueError, IS, f, [(chr(97 + i), 1, 1) for i in range(9)])
    for bad in ('ab', None, 5, ('a', 1), ('a', 1, 1, 1), (), {'a': 1}, L(['a', 1, 1]), T(('a', 1, 1))):
        _raises(ValueError, IE, f, [bad])
        _raises(ValueError, IE, f, [('b', 1, 1), bad])
    for bad in ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661'):
        _raises(ValueError, SK, f, [(bad, 1, 1)])
        _raises(ValueError, SK, f, [('b', 1, 1), (bad, 1, 1)])
    f([('A~ z', 1, 1)])
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, AS, f, [('a', bad, 0)])
        _raises(ValueError, AS, f, [('b', 1, 1), ('a', bad, 0)])
    for bad in (-1, 3, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, CO, f, [('a', 2, bad)])
        _raises(ValueError, CO, f, [('b', 2, 1), ('a', 2, bad)])
    f([('a', 1, 0)])
    f([('a', 20, 20)])
    _raises(ValueError, DS, f, [('a', 1, 1), ('a', 1, 1)])
    _raises(ValueError, TH, f, None, I(1))
    _raises(TypeError, IT, f, None)
    _raises(ValueError, IS, f, [])
    _raises(ValueError, IE, f, [1])
    _raises(ValueError, SK, f, [(1, 0, 0)])
    _raises(ValueError, AS, f, [('a', 0, 9)])
    _raises(ValueError, CO, f, [('a', 1, 9), ('a', 1, 9)])
    _raises(ValueError, DS, f, [('a', 1, 1), ('a', 1, 1)])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("threshold=50", "threshold=51"),
    ("type(threshold) is not int or not 1 <= threshold <= 100", "not isinstance(threshold, int) or not 1 <= threshold <= 100"),
    ("type(threshold) is not int or not 1 <= threshold <= 100", "isinstance(threshold, bool) or not isinstance(threshold, int) or not 1 <= threshold <= 100"),
    ("not 1 <= threshold <= 100", "not 0 <= threshold <= 100"),
    ("not 1 <= threshold <= 100", "not 1 <= threshold < 100"),
    ("not 1 <= threshold <= 100", "not 1 <= threshold <= 101"),
    ("type(items) not in (list, tuple)", "not isinstance(items, (list, tuple))"),
    ("not 1 <= len(items) <= 8", "not 0 <= len(items) <= 8"),
    ("not 1 <= len(items) <= 8", "not 1 <= len(items) < 8"),
    ("not 1 <= len(items) <= 8", "not 1 <= len(items) <= 9"),
    ("type(it) not in (list, tuple) or len(it) != 3", "not isinstance(it, (list, tuple)) or len(it) != 3"),
    ("type(it) not in (list, tuple) or len(it) != 3", "type(it) not in (list, tuple) or len(it) > 3"),
    ("type(it) not in (list, tuple) or len(it) != 3", "type(it) not in (list, tuple) or len(it) < 3"),
    ("type(skill) is not str or not skill.isascii() or not 1 <= len(skill) <= 12", "not isinstance(skill, str) or not skill.isascii() or not 1 <= len(skill) <= 12"),
    ("type(skill) is not str or not skill.isascii() or not 1 <= len(skill) <= 12", "type(skill) is not str or not 1 <= len(skill) <= 12"),
    ("type(skill) is not str or not skill.isascii() or not 1 <= len(skill) <= 12", "type(skill) is not str or not skill.isalnum() or not 1 <= len(skill) <= 12"),
    ("type(skill) is not str or not skill.isascii() or not 1 <= len(skill) <= 12", "type(skill) is not str or not skill.isascii() or not 0 <= len(skill) <= 12"),
    ("type(skill) is not str or not skill.isascii() or not 1 <= len(skill) <= 12", "type(skill) is not str or not skill.isascii() or not 1 <= len(skill) < 12"),
    ("type(skill) is not str or not skill.isascii() or not 1 <= len(skill) <= 12", "type(skill) is not str or not skill.isascii() or not 1 <= len(skill) <= 13"),
    ("type(asked) is not int or not 1 <= asked <= 20", "not isinstance(asked, int) or not 1 <= asked <= 20"),
    ("type(asked) is not int or not 1 <= asked <= 20", "isinstance(asked, bool) or not isinstance(asked, int) or not 1 <= asked <= 20"),
    ("not 1 <= asked <= 20", "not 0 <= asked <= 20"),
    ("not 1 <= asked <= 20", "not 1 <= asked < 20"),
    ("not 1 <= asked <= 20", "not 1 <= asked <= 21"),
    ("type(correct) is not int or not 0 <= correct <= asked", "not isinstance(correct, int) or not 0 <= correct <= asked"),
    ("type(correct) is not int or not 0 <= correct <= asked", "isinstance(correct, bool) or not isinstance(correct, int) or not 0 <= correct <= asked"),
    ("not 0 <= correct <= asked", "not 1 <= correct <= asked"),
    ("not 0 <= correct <= asked", "not -1 <= correct <= asked"),
    ("not 0 <= correct <= asked", "not 0 <= correct < asked"),
    ("not 0 <= correct <= asked", "not 0 <= correct <= asked + 1"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("r[2] * 100 < threshold * r[1]", "r[2] * 100 <= threshold * r[1]"),
    ("r[2] * 100 < threshold * r[1]", "r[2] * 100 // r[1] < threshold - 1"),
    ("r[2] * 100 < threshold * r[1]", "r[2] * 100 > threshold * r[1]"),
    ("left = x[2] * y[1]", "left = x[2] * y[2]"),
    ("right = y[2] * x[1]", "right = y[2] * x[2]"),
    ("return -1 if left < right else 1", "return 1 if left < right else -1"),
    ("return -1 if x[0] < y[0] else (1 if x[0] > y[0] else 0)", "return -1 if x[0] > y[0] else (1 if x[0] < y[0] else 0)"),
    ("return -1 if x[0] < y[0] else (1 if x[0] > y[0] else 0)", "return 0"),
    ("if left != right:", "if left // 1 != right // 1 and False:"),
    ("gaps.sort(key=cmp_to_key(_by_share))", "gaps.sort(key=lambda r: (r[2] * 100 // r[1], r[0]))"),
    ("gaps.sort(key=cmp_to_key(_by_share))", "gaps.sort(key=lambda r: r[0])"),
    ("gaps.sort(key=cmp_to_key(_by_share))", "gaps.sort(key=cmp_to_key(_by_share), reverse=True)"),
    ("c * 100 // a) for s, a, c in gaps", "(c * 100 + a - 1) // a) for s, a, c in gaps"),
    ("c * 100 // a) for s, a, c in gaps", "round(c * 100 / a)) for s, a, c in gaps"),
    ("'secure': len(rows) - len(gaps)", "'secure': len(rows)"),
    ("'clear': not gaps", "'clear': len(gaps) < 2"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
