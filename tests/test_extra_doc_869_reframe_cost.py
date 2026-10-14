import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import reframe_cost as mod

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
    assert mod.SCOPE == 'PARTIAL: restates a supplied total per supplied unit count, no perspective is changed'
    assert len(mod.NOT_CLAIMED) == 5 and 'persuasion effect' in mod.NOT_CLAIMED and 'fair unit choice' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Reframing - Changes perspective' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(tot, us):
    """Independent: bisect for the whole-cent share, order the units by repeated selection."""
    def split(t, c):
        lo, hi = 0, t
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if mid * c <= t:
                lo = mid
            else:
                hi = mid - 1
        return lo, t - lo * c
    left = list(us)
    ordered = []
    while left:
        pick = left[0]
        for u in left[1:]:
            if u[1] > pick[1] or (u[1] == pick[1] and u[0] < pick[0]):
                pick = u
        ordered.append(pick)
        left.remove(pick)
    frames = []
    for n, c in ordered:
        q, r = split(tot, c)
        frames.append((n, q, r))
    return {'frames': frames, 'gentlest': frames[0][0], 'steepest': frames[-1][0], 'spread': frames[-1][1] - frames[0][1]}


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
    f = m.reframe_cost
    assert f(100, [('day', 1)]) == {'frames': [('day', 100, 0)], 'gentlest': 'day', 'steepest': 'day', 'spread': 0}
    assert f(1, [('a', 1)]) == {'frames': [('a', 1, 0)], 'gentlest': 'a', 'steepest': 'a', 'spread': 0}
    assert f(1, [('a', 2)]) == {'frames': [('a', 0, 1)], 'gentlest': 'a', 'steepest': 'a', 'spread': 0}
    assert f(10, [('a', 3)])['frames'] == [('a', 3, 1)]
    assert f(10, [('a', 5)])['frames'] == [('a', 2, 0)]
    assert f(10, [('a', 10)])['frames'] == [('a', 1, 0)] and f(10, [('a', 11)])['frames'] == [('a', 0, 10)]
    r = f(36500, [('year', 1), ('month', 12), ('week', 52), ('day', 365)])
    assert r == {'frames': [('day', 100, 0), ('week', 701, 48), ('month', 3041, 8), ('year', 36500, 0)], 'gentlest': 'day', 'steepest': 'year', 'spread': 36400}
    assert f(36500, [('day', 365), ('year', 1), ('week', 52), ('month', 12)]) == r
    # ties on count are ordered by unit name
    assert f(100, [('z', 4), ('b', 4), ('m', 4)])['frames'] == [('b', 25, 0), ('m', 25, 0), ('z', 25, 0)]
    assert f(100, [('z', 4), ('b', 3), ('m', 4)])['frames'] == [('m', 25, 0), ('z', 25, 0), ('b', 33, 1)]
    assert f(100, [('z', 4), ('b', 3), ('m', 4)])['gentlest'] == 'm' and f(100, [('z', 4), ('b', 3), ('m', 4)])['steepest'] == 'b'
    assert f(999999, [('a', 10000), ('b', 1)]) == {'frames': [('a', 99, 9999), ('b', 999999, 0)], 'gentlest': 'a', 'steepest': 'b', 'spread': 999900}
    assert f(1000000, [('a', 10000)])['frames'] == [('a', 100, 0)]
    # mixed list and tuple entries, in both orders
    base = f(100, [('a', 3), ('b', 7)])
    assert f(100, [('a', 3), ['b', 7]]) == base and f(100, [['a', 3], ('b', 7)]) == base and f(100, (['a', 3], ['b', 7])) == base
    assert f(100, [('x' * 12, 3), ('A~ z', 7)])['frames'][0][0] == 'A~ z'
    assert len(f(100, [(chr(97 + i), i + 1) for i in range(5)])['frames']) == 5
    rng = random.Random(869)
    for _ in range(1500):
        tot = rng.choice((rng.randint(1, 50), rng.randint(1, 1000000)))
        us = [(chr(97 + i), rng.choice((rng.randint(1, 12), rng.randint(1, 10000)))) for i in range(rng.randint(1, 5))]
        rng.shuffle(us)
        us = [rng.choice((list, tuple))(u) for u in us]
        assert f(tot, us) == _oracle(tot, us), (tot, us)


def _late(m):
    f = m.reframe_cost
    TO = 'total must be a nonbool integer between 1 and 1000000'
    UT = 'units must be a list or tuple'
    US = 'units must contain 1 to 5 entries'
    UE = 'each entry must be a (unit, count) tuple'
    UN = 'each unit must be a printable ASCII string of 1 to 12 characters'
    CN = 'count must be a nonbool integer between 1 and 10000'
    UD = 'units must be distinct'
    ok = [('a', 1)]
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661',
             '\n', 'a\n', '\ta', 'a\x00', '\x7f', 'a\r', '\x1b[0m', 'a\x0b')
    for bad in (0, 1000001, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TO, f, bad, ok)
    f(1, ok)
    f(1000000, ok)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, UT, f, 1, bad)
    _raises(ValueError, US, f, 1, [])
    _raises(ValueError, US, f, 1, [(chr(97 + i), 1) for i in range(6)])
    f(1, [(chr(97 + i), 1) for i in range(5)])
    for bad in ('ab', None, 5, ('a',), ('a', 1, 1), (), {'a': 1}, L(['a', 1]), T(('a', 1))):
        _raises(ValueError, UE, f, 1, [bad])
        _raises(ValueError, UE, f, 1, [('b', 1), bad])
    for bad in names:
        _raises(ValueError, UN, f, 1, [(bad, 1)])
        _raises(ValueError, UN, f, 1, [('b', 1), (bad, 1)])
    f(1, [(' ', 1), ('A~ z', 2)])
    for bad in (0, 10001, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, CN, f, 1, [('a', bad)])
        _raises(ValueError, CN, f, 1, [('b', 1), ('a', bad)])
    f(1, [('a', 10000)])
    _raises(ValueError, UD, f, 1, [('a', 1), ('a', 2)])
    _raises(ValueError, TO, f, None, None)
    _raises(TypeError, UT, f, 1, None)
    _raises(ValueError, US, f, 1, [])
    _raises(ValueError, UE, f, 1, [1])
    _raises(ValueError, UN, f, 1, [(1, 0)])
    _raises(ValueError, CN, f, 1, [('a', 0), ('a', 0)])
    _raises(ValueError, UD, f, 1, [('a', 1), ('a', 2)])


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


LB = "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"
MUTANTS = [
    (LB, "isinstance(x, str) and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isalnum() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 0 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) < 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 13"),
    ("type(units) not in (list, tuple)", "not isinstance(units, (list, tuple))"),
    ("not 1 <= len(units) <= 5", "not 0 <= len(units) <= 5"),
    ("not 1 <= len(units) <= 5", "not 1 <= len(units) < 5"),
    ("not 1 <= len(units) <= 5", "not 1 <= len(units) <= 6"),
    ("type(u) not in (list, tuple) or len(u) != 2", "not isinstance(u, (list, tuple)) or len(u) != 2"),
    ("type(u) not in (list, tuple) or len(u) != 2", "type(u) not in (list, tuple) or len(u) > 2"),
    ("type(u) not in (list, tuple) or len(u) != 2", "type(u) not in (list, tuple) or len(u) < 2"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("rows.sort(key=lambda r: (-r[1], r[0]))", "rows.sort(key=lambda r: (r[1], r[0]))"),
    ("rows.sort(key=lambda r: (-r[1], r[0]))", "rows.sort(key=lambda r: (-r[1], r[0]), reverse=True)"),
    ("rows.sort(key=lambda r: (-r[1], r[0]))", "rows.sort(key=lambda r: -r[1])"),
    ("rows.sort(key=lambda r: (-r[1], r[0]))", "rows.sort(key=lambda r: r[0])"),
    ("rows.sort(key=lambda r: (-r[1], r[0]))", "rows.sort(key=lambda r: (-r[1], -ord(r[0][0])))"),
    ("total // count", "-(-total // count)"),
    ("total // count", "round(total / count)"),
    ("total // count", "total // (count + 1)"),
    ("total % count", "count - total % count"),
    ("total % count", "total % (count + 1)"),
    ("'gentlest': frames[0][0]", "'gentlest': frames[-1][0]"),
    ("'steepest': frames[-1][0]", "'steepest': frames[0][0]"),
    ("'spread': frames[-1][1] - frames[0][1]", "'spread': frames[0][1] - frames[-1][1]"),
    ("'spread': frames[-1][1] - frames[0][1]", "'spread': frames[-1][2] - frames[0][2]"),
]
for _v, _lo, _hi in (('total', 1, 1000000), ('count', 1, 10000)):
    MUTANTS += _ints(_v, _lo, _hi)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
