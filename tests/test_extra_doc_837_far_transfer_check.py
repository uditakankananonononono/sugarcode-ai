import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import far_transfer_check as mod

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
    assert mod.SCOPE == 'PARTIAL: scores supplied tasks that share no supplied taught feature, no learner transfers'
    assert len(mod.NOT_CLAIMED) == 5 and 'true task difference' in mod.NOT_CLAIMED and 'real far transfer' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Far Transfer - Applies to different' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(td, ts, ps):
    """Independent: set intersection for disjointness, and the majority test by counting pairs of passes."""
    tdset = frozenset(td)
    names, passed, shared = [], 0, 0
    for n, fs, s in ts:
        if tdset & frozenset(fs):
            shared += 1
            continue
        names.append(n)
        if s >= ps:
            passed += 1
    k = len(names)
    pct = 0
    while k and (pct + 1) * k <= passed * 100:
        pct += 1
    return {'far': names, 'far_passed': passed, 'shared': shared, 'far_percent': pct,
            'reached': k > 0 and passed > k - passed}


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
    f = m.far_transfer_check
    assert f(['a'], [('x', ['b'], 9)]) == {'far': ['x'], 'far_passed': 1, 'shared': 0, 'far_percent': 100, 'reached': True}
    assert f(['a'], [('x', ['a'], 9)]) == {'far': [], 'far_passed': 0, 'shared': 1, 'far_percent': 0, 'reached': False}
    assert f(['a'], [('x', ['a', 'b'], 9)])['shared'] == 1
    assert f(['a'], [('x', ['b', 'c', 'd', 'a'], 9)])['far'] == []
    assert f(['a'], [('x', ['b'], 0)]) == {'far': ['x'], 'far_passed': 0, 'shared': 0, 'far_percent': 0, 'reached': False}
    # default pass_score 6: 5 fails, 6 passes; 5 and 7 as explicit values move the edge
    assert f(['a'], [('x', ['b'], 5)])['far_passed'] == 0 and f(['a'], [('x', ['b'], 6)])['far_passed'] == 1
    assert f(['a'], [('x', ['b'], 5)], 5)['far_passed'] == 1 and f(['a'], [('x', ['b'], 6)], 7)['far_passed'] == 0
    assert f(['a'], [('x', ['b'], 6)]) == f(['a'], [('x', ['b'], 6)], 6)
    assert f(['a'], [('x', ['b'], 10)], 10)['far_passed'] == 1 and f(['a'], [('x', ['b'], 9)], 10)['far_passed'] == 0
    assert f(['a'], [('x', ['b'], 1)], 1)['far_passed'] == 1
    # strict majority: 1 of 2 is not reached, 2 of 3 is, 1 of 3 is not
    assert f(['a'], [('x', ['b'], 9), ('y', ['c'], 0)])['reached'] is False
    assert f(['a'], [('x', ['b'], 9), ('y', ['c'], 9), ('z', ['d'], 0)]) == {'far': ['x', 'y', 'z'], 'far_passed': 2, 'shared': 0, 'far_percent': 66, 'reached': True}
    assert f(['a'], [('x', ['b'], 9), ('y', ['c'], 0), ('z', ['d'], 0)])['far_percent'] == 33
    # shared tasks do not count in the far share
    r = f(['a', 'b'], [('p', ['a'], 9), ('q', ['c'], 9), ('r', ['b', 'd'], 9), ('s', ['e'], 1)])
    assert r == {'far': ['q', 's'], 'far_passed': 1, 'shared': 2, 'far_percent': 50, 'reached': False}
    # order is input order, not name order
    assert f(['a'], [('z', ['b'], 9), ('c', ['c'], 9)])['far'] == ['z', 'c']
    assert f(('a',), (('x', ('b',), 9), ['y', ['c'], 9]))['far'] == ['x', 'y']
    assert f(['a'], [('x', ['A'], 9)])['far'] == ['x']
    assert f(['k' * 12], [('x' * 12, ['k' * 12], 9), ('y', ['j' * 12], 9)])['far'] == ['y']
    assert f(list('abcdef'), [('x', ['f'], 9), ('y', ['g'], 9)])['far'] == ['y']
    assert len(f(['a'], [(chr(98 + i), ['b'], 9) for i in range(8)])['far']) == 8
    rng = random.Random(837)
    pool = 'abcdefghij'
    for _ in range(800):
        td = rng.sample(pool, rng.randint(1, 6))
        ts = [(chr(97 + i), rng.sample(pool, rng.randint(1, 4)), rng.randint(0, 10)) for i in range(rng.randint(1, 8))]
        ts = [(n, rng.choice((list, tuple))(fs), s) for n, fs, s in ts]
        ps = rng.randint(1, 10)
        assert f(td, ts, ps) == _oracle(td, ts, ps), (td, ts, ps)
        assert f(td, ts) == _oracle(td, ts, 6)


def _late(m):
    f = m.far_transfer_check
    PS = 'pass_score must be a nonbool integer between 1 and 10'
    TT = 'taught must be a list or tuple'
    TS = 'taught must contain 1 to 6 entries'
    TE = 'each taught entry must be an ASCII string of 1 to 12 characters'
    TD = 'taught entries must be distinct'
    KT = 'tasks must be a list or tuple'
    KS = 'tasks must contain 1 to 8 entries'
    KE = 'each task must be a (name, features, score) tuple'
    NM = 'each name must be an ASCII string of 1 to 12 characters'
    FT = 'features must be a list or tuple'
    FS = 'features must contain 1 to 4 entries'
    FE = 'each feature must be an ASCII string of 1 to 12 characters'
    FD = 'features must be distinct'
    SC = 'score must be a nonbool integer between 0 and 10'
    ND = 'names must be distinct'
    ok = [('x', ['b'], 1)]
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661')
    badint = lambda lo, hi: (lo - 1, hi + 1, True, False, 1.0, '1', None, I(lo), LyingI(lo), LyingI(10 ** 30), I(10 ** 30))
    for bad in badint(1, 10):
        _raises(ValueError, PS, f, ['a'], ok, bad)
    f(['a'], ok, 1)
    f(['a'], ok, 10)
    for bad in ('ab', None, 5, {}, L(['a']), T(['a']), L(), T()):
        _raises(TypeError, TT, f, bad, ok)
    _raises(ValueError, TS, f, [], ok)
    _raises(ValueError, TS, f, list('abcdefg'), ok)
    for bad in names:
        _raises(ValueError, TE, f, [bad], ok)
        _raises(ValueError, TE, f, ['a', bad], ok)
    f(['A~ z'], ok)
    _raises(ValueError, TD, f, ['a', 'a'], ok)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, KT, f, ['a'], bad)
    _raises(ValueError, KS, f, ['a'], [])
    _raises(ValueError, KS, f, ['a'], [(chr(97 + i), ['b'], 1) for i in range(9)])
    for bad in ('ab', None, 5, ('x', ['b']), ('x', ['b'], 1, 1), (), {'x': 1}, L(['x', ['b'], 1]), T(('x', ['b'], 1))):
        _raises(ValueError, KE, f, ['a'], [bad])
        _raises(ValueError, KE, f, ['a'], [('y', ['b'], 1), bad])
    for bad in names:
        _raises(ValueError, NM, f, ['a'], [(bad, ['b'], 1)])
        _raises(ValueError, NM, f, ['a'], [('y', ['b'], 1), (bad, ['b'], 1)])
    f(['a'], [('A~ z', ['b'], 1)])
    for bad in ('ab', None, 5, {}, {'b'}, L(['b']), T(['b']), L(), T()):
        _raises(ValueError, FT, f, ['a'], [('x', bad, 1)])
        _raises(ValueError, FT, f, ['a'], [('y', ['b'], 1), ('x', bad, 1)])
    _raises(ValueError, FS, f, ['a'], [('x', [], 1)])
    _raises(ValueError, FS, f, ['a'], [('x', list('bcdef'), 1)])
    f(['a'], [('x', list('bcde'), 1)])
    for bad in names:
        _raises(ValueError, FE, f, ['a'], [('x', [bad], 1)])
        _raises(ValueError, FE, f, ['a'], [('y', ['b'], 1), ('x', ['b', bad], 1)])
    f(['a'], [('x', ['A~ z'], 1)])
    _raises(ValueError, FD, f, ['a'], [('x', ['b', 'b'], 1)])
    for bad in badint(0, 10):
        _raises(ValueError, SC, f, ['a'], [('x', ['b'], bad)])
        _raises(ValueError, SC, f, ['a'], [('y', ['b'], 1), ('x', ['b'], bad)])
    f(['a'], [('x', ['b'], 0)])
    f(['a'], [('x', ['b'], 10)])
    _raises(ValueError, ND, f, ['a'], [('x', ['b'], 1), ('x', ['b'], 1)])
    _raises(ValueError, PS, f, None, None, 0)
    _raises(TypeError, TT, f, None, None)
    _raises(ValueError, TS, f, [], None)
    _raises(ValueError, TE, f, [1, 1], None)
    _raises(ValueError, TD, f, ['a', 'a'], None)
    _raises(TypeError, KT, f, ['a'], None)
    _raises(ValueError, KS, f, ['a'], [])
    _raises(ValueError, KE, f, ['a'], [1])
    _raises(ValueError, NM, f, ['a'], [(1, 5, 99)])
    _raises(ValueError, FT, f, ['a'], [('x', 5, 99)])
    _raises(ValueError, FS, f, ['a'], [('x', [], 99)])
    _raises(ValueError, FE, f, ['a'], [('x', [1, 1], 99)])
    _raises(ValueError, FD, f, ['a'], [('x', ['b', 'b'], 99)])
    _raises(ValueError, SC, f, ['a'], [('x', ['b'], 99), ('x', ['b'], 99)])
    _raises(ValueError, ND, f, ['a'], [('x', ['b'], 1), ('x', ['b'], 1)])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def _ints(var, lo, hi):
    base = "type(%s) is not int or not %s <= %s <= %s" % (var, lo, var, hi)
    return [
        (base, "not isinstance(%s, int) or not %s <= %s <= %s" % (var, lo, var, hi)),
        (base, "isinstance(%s, bool) or not isinstance(%s, int) or not %s <= %s <= %s" % (var, var, lo, var, hi)),
        (base, "type(%s) is not int or not %s <= %s <= %s" % (var, lo - 1, var, hi)),
        (base, "type(%s) is not int or not %s <= %s <= %s" % (var, lo + 1, var, hi)),
        (base, "type(%s) is not int or not %s <= %s <= %s" % (var, lo, var, hi - 1)),
        (base, "type(%s) is not int or not %s <= %s <= %s" % (var, lo, var, hi + 1)),
    ]


LB = "type(x) is str and x.isascii() and 1 <= len(x) <= 12"
MUTANTS = [
    ("pass_score=6", "pass_score=5"),
    ("pass_score=6", "pass_score=7"),
    (LB, "isinstance(x, str) and x.isascii() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isalnum() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 0 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) < 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) <= 13"),
    ("type(taught) not in (list, tuple)", "not isinstance(taught, (list, tuple))"),
    ("not 1 <= len(taught) <= 6", "not 0 <= len(taught) <= 6"),
    ("not 1 <= len(taught) <= 6", "not 1 <= len(taught) < 6"),
    ("not 1 <= len(taught) <= 6", "not 1 <= len(taught) <= 7"),
    ("if len(set(taught)) != len(taught):", "if False:"),
    ("type(tasks) not in (list, tuple)", "not isinstance(tasks, (list, tuple))"),
    ("not 1 <= len(tasks) <= 8", "not 0 <= len(tasks) <= 8"),
    ("not 1 <= len(tasks) <= 8", "not 1 <= len(tasks) < 8"),
    ("not 1 <= len(tasks) <= 8", "not 1 <= len(tasks) <= 9"),
    ("type(tk) not in (list, tuple) or len(tk) != 3", "not isinstance(tk, (list, tuple)) or len(tk) != 3"),
    ("type(tk) not in (list, tuple) or len(tk) != 3", "type(tk) not in (list, tuple) or len(tk) > 3"),
    ("type(tk) not in (list, tuple) or len(tk) != 3", "type(tk) not in (list, tuple) or len(tk) < 3"),
    ("type(features) not in (list, tuple)", "not isinstance(features, (list, tuple))"),
    ("not 1 <= len(features) <= 4", "not 0 <= len(features) <= 4"),
    ("not 1 <= len(features) <= 4", "not 1 <= len(features) < 4"),
    ("not 1 <= len(features) <= 4", "not 1 <= len(features) <= 5"),
    ("if len(set(features)) != len(features):", "if False:"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("not any(x in taught for x in f)", "not all(x in taught for x in f)"),
    ("not any(x in taught for x in f)", "not (f[0] in taught)"),
    ("not any(x in taught for x in f)", "not (f[-1] in taught)"),
    ("not any(x in taught for x in f)", "any(x in taught for x in f)"),
    ("if s >= pass_score", "if s > pass_score"),
    ("passed = sum(1 for _, s in far", "passed = sum(s for _, s in far"),
    ("'shared': len(rows) - len(far)", "'shared': len(far)"),
    ("'far': [n for n, _ in far]", "'far': sorted(n for n, _ in far)"),
    ("passed * 100 // len(far) if far else 0", "(passed * 100 + len(far) - 1) // len(far) if far else 0"),
    ("passed * 100 // len(far) if far else 0", "round(passed * 100 / len(far)) if far else 0"),
    ("passed * 100 // len(far) if far else 0", "passed * 100 // len(far) if far else 100"),
    ("'reached': passed * 2 > len(far)", "'reached': passed * 2 >= len(far)"),
    ("'reached': passed * 2 > len(far)", "'reached': passed * 3 > len(far)"),
    ("'reached': passed * 2 > len(far)", "'reached': passed > 0"),
]
for _v, _lo, _hi in (('pass_score', 1, 10), ('score', 0, 10)):
    MUTANTS += _ints(_v, _lo, _hi)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
