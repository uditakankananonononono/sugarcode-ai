import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import history_context as mod

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
    assert mod.SCOPE == 'PARTIAL: orders supplied events around a supplied one by year gap, no history is interpreted'
    assert len(mod.NOT_CLAIMED) == 5 and 'source criticism' in mod.NOT_CLAIMED and 'causation' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Historical Thinking - Contextualizes' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(ev, fc, wd):
    """Independent: chronological scan of a list sorted by (year, name), measuring gaps from the focus position."""
    ordered = sorted((y, n) for n, y in ev)
    fy = [y for y, n in ordered if n == fc][0]
    bef, aft, same, out = [], [], [], 0
    for y, n in ordered:
        if n == fc:
            continue
        gap = y - fy
        if abs(gap) > wd:
            out += 1
        elif gap < 0:
            bef.append((n, -gap))
        elif gap > 0:
            aft.append((n, gap))
        else:
            same.append(n)
    bef.sort(key=lambda r: (r[1], r[0]))
    rank = 1
    for y, n in ordered:
        if y < fy:
            rank += 1
    return {'focus': fc, 'year': fy, 'before': bef, 'after': aft, 'same_year': same, 'outside': out, 'rank': rank}


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
    f = m.history_context
    assert f([('a', 1900), ('b', 1905)], 'a') == {'focus': 'a', 'year': 1900, 'before': [], 'after': [('b', 5)], 'same_year': [], 'outside': 0, 'rank': 1}
    assert f([('a', 1900), ('b', 1905)], 'b') == {'focus': 'b', 'year': 1905, 'before': [('a', 5)], 'after': [], 'same_year': [], 'outside': 0, 'rank': 2}
    assert f([('a', 1900), ('b', 1900)], 'a') == {'focus': 'a', 'year': 1900, 'before': [], 'after': [], 'same_year': ['b'], 'outside': 0, 'rank': 1}
    assert f([('a', 1900), ('b', 1900)], 'b')['rank'] == 1
    # default window 10: gap 10 is inside, 11 is outside; windows 9, 11 and 100 move the edge
    ev = [('f', 1950), ('p', 1940), ('q', 1961), ('r', 1939), ('s', 1960)]
    r = f(ev, 'f')
    assert r['before'] == [('p', 10)] and r['after'] == [('s', 10)] and r['outside'] == 2 and r['rank'] == 3
    assert f(ev, 'f') == f(ev, 'f', 10)
    r = f(ev, 'f', 9)
    assert r['before'] == [] and r['after'] == [] and r['outside'] == 4
    assert f(ev, 'f', 11)['before'] == [('p', 10), ('r', 11)] and f(ev, 'f', 11)['after'] == [('s', 10), ('q', 11)] and f(ev, 'f', 11)['outside'] == 0
    assert f(ev, 'f', 100)['outside'] == 0
    # nearest first, ties by name, rank counts strictly earlier years only
    ev = [('f', 2000), ('z', 1998), ('m', 1998), ('c', 1999), ('k', 2000), ('d', 2002), ('e', 2002)]
    r = f(ev, 'f')
    assert r == {'focus': 'f', 'year': 2000, 'before': [('c', 1), ('m', 2), ('z', 2)], 'after': [('d', 2), ('e', 2)], 'same_year': ['k'], 'outside': 0, 'rank': 4}
    assert f(ev[::-1], 'f') == r
    assert f(ev, 'z')['rank'] == 1 and f(ev, 'm')['rank'] == 1 and f(ev, 'd')['rank'] == 6
    assert f([('x' * 12, 1), ('y', 2100)], 'x' * 12, 100)['outside'] == 1
    assert f((['a', 1], ('b', 2100)), 'b')['year'] == 2100
    assert f([('A~ z 9', 5), ('b', 6)], 'A~ z 9')['after'] == [('b', 1)]
    assert len(f([(chr(97 + i), 100 + i) for i in range(8)], 'a', 100)['after']) == 7
    rng = random.Random(862)
    for _ in range(1000):
        n = rng.randint(2, 8)
        ev2 = [(chr(97 + i), rng.randint(1, 40)) for i in range(n)]
        rng.shuffle(ev2)
        fc = rng.choice(ev2)[0]
        wd = rng.randint(1, 100) if rng.random() < 0.5 else rng.randint(1, 12)
        ev2 = [rng.choice((list, tuple))(e) for e in ev2]
        assert f(ev2, fc, wd) == _oracle(ev2, fc, wd), (ev2, fc, wd)
        assert f(ev2, fc) == _oracle(ev2, fc, 10)


def _late(m):
    f = m.history_context
    WI = 'window must be a nonbool integer between 1 and 100'
    ET = 'events must be a list or tuple'
    ES = 'events must contain 2 to 8 entries'
    EE = 'each event must be a (name, year) tuple'
    NM = 'each name must be a printable ASCII string of 1 to 12 characters'
    YR = 'year must be a nonbool integer between 1 and 2100'
    ND = 'names must be distinct'
    FT = 'focus must be a printable ASCII string of 1 to 12 characters'
    FM = 'focus must name one of the events'
    ok = [('a', 1), ('b', 2)]
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661',
             '\n', 'a\n', '\ta', 'a\x00', '\x7f', 'a\r', '\x1b[0m', 'a\x0b')
    for bad in (0, 101, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, WI, f, ok, 'a', bad)
    f(ok, 'a', 1)
    f(ok, 'a', 100)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, ET, f, bad, 'a')
    _raises(ValueError, ES, f, [('a', 1)], 'a')
    _raises(ValueError, ES, f, [], 'a')
    _raises(ValueError, ES, f, [(chr(97 + i), 1) for i in range(9)], 'a')
    f([(chr(97 + i), 1) for i in range(8)], 'a')
    for bad in ('ab', None, 5, ('a',), ('a', 1, 1), (), {'a': 1}, L(['a', 1]), T(('a', 1))):
        _raises(ValueError, EE, f, [bad, ('b', 2)], 'a')
        _raises(ValueError, EE, f, [('b', 2), bad], 'a')
    for bad in names:
        _raises(ValueError, NM, f, [(bad, 1), ('b', 2)], 'b')
        _raises(ValueError, NM, f, [('b', 2), (bad, 1)], 'b')
    f([('A~ z', 1), (' ', 2)], ' ')
    for bad in (0, 2101, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, YR, f, [('a', bad), ('b', 2)], 'b')
        _raises(ValueError, YR, f, [('b', 2), ('a', bad)], 'b')
    f([('a', 1), ('b', 2100)], 'a')
    _raises(ValueError, ND, f, [('a', 1), ('a', 2)], 'a')
    for bad in names:
        _raises(ValueError, FT, f, ok, bad)
    _raises(ValueError, FM, f, ok, 'c')
    _raises(ValueError, FM, f, ok, 'A')
    _raises(ValueError, WI, f, None, None, 0)
    _raises(TypeError, ET, f, None, None)
    _raises(ValueError, ES, f, [], None)
    _raises(ValueError, EE, f, [1, 2], None)
    _raises(ValueError, NM, f, [(1, 0), ('b', 2)], None)
    _raises(ValueError, YR, f, [('a', 0), ('b', 2)], None)
    _raises(ValueError, ND, f, [('a', 1), ('a', 2)], None)
    _raises(ValueError, FT, f, ok, None)
    _raises(ValueError, FM, f, ok, 'zz')


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


LB = "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"
MUTANTS = [
    ("window=10", "window=9"),
    ("window=10", "window=11"),
    (LB, "isinstance(x, str) and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isalnum() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 0 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) < 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 13"),
    ("type(window) is not int or not 1 <= window <= 100", "not isinstance(window, int) or not 1 <= window <= 100"),
    ("type(window) is not int or not 1 <= window <= 100", "isinstance(window, bool) or not isinstance(window, int) or not 1 <= window <= 100"),
    ("not 1 <= window <= 100", "not 0 <= window <= 100"),
    ("not 1 <= window <= 100", "not 1 <= window < 100"),
    ("not 1 <= window <= 100", "not 1 <= window <= 101"),
    ("type(events) not in (list, tuple)", "not isinstance(events, (list, tuple))"),
    ("not 2 <= len(events) <= 8", "not 1 <= len(events) <= 8"),
    ("not 2 <= len(events) <= 8", "not 3 <= len(events) <= 8"),
    ("not 2 <= len(events) <= 8", "not 2 <= len(events) < 8"),
    ("not 2 <= len(events) <= 8", "not 2 <= len(events) <= 9"),
    ("type(e) not in (list, tuple) or len(e) != 2", "not isinstance(e, (list, tuple)) or len(e) != 2"),
    ("type(e) not in (list, tuple) or len(e) != 2", "type(e) not in (list, tuple) or len(e) > 2"),
    ("type(e) not in (list, tuple) or len(e) != 2", "type(e) not in (list, tuple) or len(e) < 2"),
    ("type(year) is not int or not 1 <= year <= 2100", "not isinstance(year, int) or not 1 <= year <= 2100"),
    ("type(year) is not int or not 1 <= year <= 2100", "isinstance(year, bool) or not isinstance(year, int) or not 1 <= year <= 2100"),
    ("not 1 <= year <= 2100", "not 0 <= year <= 2100"),
    ("not 1 <= year <= 2100", "not 1 <= year < 2100"),
    ("not 1 <= year <= 2100", "not 1 <= year <= 2101"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("if focus not in years:", "if False:"),
    ("0 < fy - y <= window)", "0 <= fy - y <= window)"),
    ("0 < fy - y <= window)", "0 < fy - y < window)"),
    ("0 < fy - y <= window)", "0 < fy - y <= window + 1)"),
    ("0 < y - fy <= window)", "0 <= y - fy <= window)"),
    ("0 < y - fy <= window)", "0 < y - fy < window)"),
    ("0 < y - fy <= window)", "0 < y - fy <= window + 1)"),
    ("before = sorted((fy - y, n)", "before = sorted((y - fy, n)"),
    ("after = sorted((y - fy, n)", "after = sorted((fy - y, n)"),
    ("'before': [(n, g) for g, n in before]", "'before': [(n, g) for g, n in before][::-1]"),
    ("'after': [(n, g) for g, n in after]", "'after': [(n, g) for g, n in after][::-1]"),
    ("sorted(n for n, y in rows if y == fy and n != focus)", "[n for n, y in rows if y == fy and n != focus]"),
    ("sorted(n for n, y in rows if y == fy and n != focus)", "sorted(n for n, y in rows if y == fy)"),
    ("abs(y - fy) > window)", "abs(y - fy) >= window)"),
    ("abs(y - fy) > window)", "(y - fy) > window)"),
    ("'rank': 1 + sum(1 for n, y in rows if y < fy)", "'rank': 1 + sum(1 for n, y in rows if y <= fy)"),
    ("'rank': 1 + sum(1 for n, y in rows if y < fy)", "'rank': sum(1 for n, y in rows if y < fy)"),
    ("'rank': 1 + sum(1 for n, y in rows if y < fy)", "'rank': 1 + sum(1 for n, y in rows if y > fy)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
