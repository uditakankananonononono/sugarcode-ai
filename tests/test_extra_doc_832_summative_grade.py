import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import summative_grade as mod

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
    assert mod.SCOPE == 'PARTIAL: exact weighted total and letter band of supplied part scores, no learner is assessed'
    assert len(mod.NOT_CLAIMED) == 5 and 'test validity' in mod.NOT_CLAIMED and 'curriculum coverage' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Summative Assessment - Assesses learning' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(ps, pm):
    """Independent: scale everything by the lcm of the possibles so only integer arithmetic is used."""
    import math
    lcm = 1
    for _, _, _, p in ps:
        lcm = lcm * p // math.gcd(lcm, p)
    parts = [(n, w * e * (lcm // p)) for n, w, e, p in ps]     # contribution * lcm
    tot = sum(v for _, v in parts)
    grade = 'F'
    for cut, g in ((60, 'D'), (70, 'C'), (80, 'B'), (90, 'A')):
        if tot >= cut * lcm:
            grade = g
    return {'breakdown': [(n, v * 10 // lcm) for n, v in parts], 'percent_tenths': tot * 10 // lcm,
            'grade': grade, 'passed': tot >= pm * lcm}


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
    f = m.summative_grade
    assert f([('a', 100, 100, 100)]) == {'breakdown': [('a', 1000)], 'percent_tenths': 1000, 'grade': 'A', 'passed': True}
    assert f([('a', 100, 0, 7)]) == {'breakdown': [('a', 0)], 'percent_tenths': 0, 'grade': 'F', 'passed': False}
    r = f([('a', 40, 3, 4), ('b', 60, 1, 3)])
    assert r == {'breakdown': [('a', 300), ('b', 200)], 'percent_tenths': 500, 'grade': 'F', 'passed': False}
    # floor of the sum differs from the sum of floors: 1/3 and 1/3 and 1/3 of weight 100/3 style
    r = f([('a', 33, 1, 3), ('b', 33, 1, 3), ('c', 34, 1, 3)])
    assert r['breakdown'] == [('a', 110), ('b', 110), ('c', 113)] and r['percent_tenths'] == 333
    r = f([('a', 50, 1, 3), ('b', 50, 1, 3)])
    assert r['breakdown'] == [('a', 166), ('b', 166)] and r['percent_tenths'] == 333
    r = f([('a', 50, 2, 3), ('b', 50, 2, 3)])
    assert r['percent_tenths'] == 666 and r['breakdown'] == [('a', 333), ('b', 333)]
    # band boundaries on the exact total
    for pct, g in ((100, 'A'), (90, 'A'), (89, 'B'), (80, 'B'), (79, 'C'), (70, 'C'), (69, 'D'), (60, 'D'), (59, 'F'), (0, 'F')):
        assert f([('a', 100, pct, 100)])['grade'] == g, pct
    # just below a boundary: 89.99.. must not round up
    assert f([('a', 50, 99, 100), ('b', 50, 8, 10)])['grade'] == 'B'
    # default pass_mark 60 versus 59 and 61
    p60 = [('a', 100, 60, 100)]
    assert f(p60)['passed'] is True and f(p60, 61)['passed'] is False and f(p60, 59)['passed'] is True and f(p60, 60) == f(p60)
    assert f([('a', 100, 59, 100)])['passed'] is False and f([('a', 100, 59, 100)], 59)['passed'] is True
    assert f([('a', 100, 100, 100)], 100)['passed'] is True and f([('a', 100, 99, 100)], 100)['passed'] is False
    assert f([('a', 100, 1, 1)], 1)['passed'] is True
    assert f((['a', 50, 1, 1], ('b', 50, 0, 1)))['percent_tenths'] == 500
    assert f([('x' * 12, 100, 1, 1)])['breakdown'][0][0] == 'x' * 12
    assert len(f([(chr(97 + i), 10 if i < 4 else 60, 1, 1) for i in range(5)])['breakdown']) == 5
    rng = random.Random(832)
    for _ in range(600):
        n = rng.randint(1, 6)
        cuts = sorted(rng.sample(range(1, 100), n - 1))
        ws = [b - a for a, b in zip([0] + cuts, cuts + [100])]
        ps = []
        for i, w in enumerate(ws):
            pos = rng.randint(1, 100)
            ps.append((chr(97 + i), w, rng.randint(0, pos), pos))
        pm = rng.randint(1, 100)
        assert f(ps, pm) == _oracle(ps, pm), (ps, pm)
        assert f(ps) == _oracle(ps, 60)


def _late(m):
    f = m.summative_grade
    PM = 'pass_mark must be a nonbool integer between 1 and 100'
    PT = 'parts must be a list or tuple'
    PS = 'parts must contain 1 to 6 entries'
    PP = 'each part must be a (name, weight, earned, possible) tuple'
    NM = 'each name must be an ASCII string of 1 to 12 characters'
    WT = 'weight must be a nonbool integer between 1 and 100'
    PO = 'possible must be a nonbool integer between 1 and 100'
    EA = 'earned must be a nonbool integer between 0 and possible'
    ND = 'names must be distinct'
    WS = 'weights must add up to 100'
    ok = [('a', 100, 1, 1)]
    for bad in (0, 101, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, PM, f, ok, bad)
    f(ok, 1)
    f(ok, 100)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, PT, f, bad)
    _raises(ValueError, PS, f, [])
    _raises(ValueError, PS, f, [(chr(97 + i), 10, 1, 1) for i in range(7)])
    for bad in ('ab', None, 5, ('a', 100, 1), ('a', 100, 1, 1, 1), (), {'a': 1}, L(['a', 100, 1, 1]), T(('a', 100, 1, 1))):
        _raises(ValueError, PP, f, [bad])
        _raises(ValueError, PP, f, [('b', 50, 1, 1), bad])
    for bad in ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661'):
        _raises(ValueError, NM, f, [(bad, 100, 1, 1)])
        _raises(ValueError, NM, f, [('b', 50, 1, 1), (bad, 50, 1, 1)])
    f([('A~ z', 100, 1, 1)])
    for bad in (0, 101, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, WT, f, [('a', bad, 1, 1)])
        _raises(ValueError, WT, f, [('b', 50, 1, 1), ('a', bad, 1, 1)])
        _raises(ValueError, PO, f, [('a', 100, 0, bad)])
        _raises(ValueError, PO, f, [('b', 50, 1, 1), ('a', 50, 0, bad)])
    for bad in (-1, 3, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, EA, f, [('a', 100, bad, 2)])
        _raises(ValueError, EA, f, [('b', 50, 1, 2), ('a', 50, bad, 2)])
    f([('a', 100, 0, 1)])
    f([('a', 100, 100, 100)])
    _raises(ValueError, ND, f, [('a', 50, 1, 1), ('a', 50, 1, 1)])
    _raises(ValueError, WS, f, [('a', 99, 1, 1)])
    _raises(ValueError, WS, f, [('a', 50, 1, 1), ('b', 51, 1, 1)])
    _raises(ValueError, WS, f, [('a', 100, 1, 1), ('b', 1, 1, 1)])
    _raises(ValueError, PM, f, None, I(1))
    _raises(TypeError, PT, f, None)
    _raises(ValueError, PS, f, [])
    _raises(ValueError, PP, f, [1])
    _raises(ValueError, NM, f, [(1, 0, 0, 0)])
    _raises(ValueError, WT, f, [('a', 0, 0, 0)])
    _raises(ValueError, PO, f, [('a', 5, 9, 0)])
    _raises(ValueError, EA, f, [('a', 5, 9, 1), ('a', 5, 9, 1)])
    _raises(ValueError, ND, f, [('a', 5, 1, 1), ('a', 5, 1, 1)])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("pass_mark=60", "pass_mark=61"),
    ("pass_mark=60", "pass_mark=59"),
    ("type(pass_mark) is not int or not 1 <= pass_mark <= 100", "not isinstance(pass_mark, int) or not 1 <= pass_mark <= 100"),
    ("type(pass_mark) is not int or not 1 <= pass_mark <= 100", "isinstance(pass_mark, bool) or not isinstance(pass_mark, int) or not 1 <= pass_mark <= 100"),
    ("not 1 <= pass_mark <= 100", "not 0 <= pass_mark <= 100"),
    ("not 1 <= pass_mark <= 100", "not 1 <= pass_mark < 100"),
    ("not 1 <= pass_mark <= 100", "not 1 <= pass_mark <= 101"),
    ("type(parts) not in (list, tuple)", "not isinstance(parts, (list, tuple))"),
    ("not 1 <= len(parts) <= 6", "not 0 <= len(parts) <= 6"),
    ("not 1 <= len(parts) <= 6", "not 1 <= len(parts) < 6"),
    ("not 1 <= len(parts) <= 6", "not 1 <= len(parts) <= 7"),
    ("type(p) not in (list, tuple) or len(p) != 4", "not isinstance(p, (list, tuple)) or len(p) != 4"),
    ("type(p) not in (list, tuple) or len(p) != 4", "type(p) not in (list, tuple) or len(p) > 4"),
    ("type(p) not in (list, tuple) or len(p) != 4", "type(p) not in (list, tuple) or len(p) < 4"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "not isinstance(name, str) or not name.isascii() or not 1 <= len(name) <= 12"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "type(name) is not str or not 1 <= len(name) <= 12"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "type(name) is not str or not name.isalnum() or not 1 <= len(name) <= 12"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "type(name) is not str or not name.isascii() or not 0 <= len(name) <= 12"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "type(name) is not str or not name.isascii() or not 1 <= len(name) < 12"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "type(name) is not str or not name.isascii() or not 1 <= len(name) <= 13"),
    ("type(weight) is not int or not 1 <= weight <= 100", "not isinstance(weight, int) or not 1 <= weight <= 100"),
    ("type(weight) is not int or not 1 <= weight <= 100", "isinstance(weight, bool) or not isinstance(weight, int) or not 1 <= weight <= 100"),
    ("not 1 <= weight <= 100", "not 0 <= weight <= 100"),
    ("not 1 <= weight <= 100", "not 1 <= weight < 100"),
    ("not 1 <= weight <= 100", "not 1 <= weight <= 101"),
    ("type(possible) is not int or not 1 <= possible <= 100", "not isinstance(possible, int) or not 1 <= possible <= 100"),
    ("type(possible) is not int or not 1 <= possible <= 100", "isinstance(possible, bool) or not isinstance(possible, int) or not 1 <= possible <= 100"),
    ("not 1 <= possible <= 100", "not 0 <= possible <= 100"),
    ("not 1 <= possible <= 100", "not 1 <= possible < 100"),
    ("not 1 <= possible <= 100", "not 1 <= possible <= 101"),
    ("type(earned) is not int or not 0 <= earned <= possible", "not isinstance(earned, int) or not 0 <= earned <= possible"),
    ("type(earned) is not int or not 0 <= earned <= possible", "isinstance(earned, bool) or not isinstance(earned, int) or not 0 <= earned <= possible"),
    ("not 0 <= earned <= possible", "not 1 <= earned <= possible"),
    ("not 0 <= earned <= possible", "not -1 <= earned <= possible"),
    ("not 0 <= earned <= possible", "not 0 <= earned < possible"),
    ("not 0 <= earned <= possible", "not 0 <= earned <= possible + 1"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("sum(r[1] for r in rows) != 100", "sum(r[1] for r in rows) > 100"),
    ("sum(r[1] for r in rows) != 100", "sum(r[1] for r in rows) < 100"),
    ("Fraction(w * e, pos)", "Fraction(w * e, pos + 1)"),
    ("Fraction(w * e, pos)", "Fraction(w * e // pos)"),
    ("if total >= 90:", "if total > 90:"),
    ("if total >= 90:", "if total >= 89:"),
    ("elif total >= 80:", "elif total > 80:"),
    ("elif total >= 70:", "elif total > 70:"),
    ("elif total >= 60:", "elif total > 60:"),
    ("elif total >= 60:", "elif total >= 59:"),
    ("(s * 10).__floor__()) for n, s in shares", "round(s * 10)) for n, s in shares"),
    ("'percent_tenths': (total * 10).__floor__()", "'percent_tenths': round(total * 10)"),
    ("'percent_tenths': (total * 10).__floor__()", "'percent_tenths': sum((s * 10).__floor__() for _, s in shares)"),
    ("'passed': total >= pass_mark", "'passed': total > pass_mark"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
