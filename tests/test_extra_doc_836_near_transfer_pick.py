import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import near_transfer_pick as mod

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
    assert mod.SCOPE == 'PARTIAL: picks supplied tasks within a reach of supplied taught positions, no learner transfers'
    assert len(mod.NOT_CLAIMED) == 5 and 'true task similarity' in mod.NOT_CLAIMED and 'real near transfer' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Near Transfer - Applies to similar' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(td, ts, rc):
    """Independent: walk outward from the task position one step at a time until a taught position is hit."""
    near, same, beyond = [], 0, 0
    for n, p, s in ts:
        d = 0
        while (p - d) not in td and (p + d) not in td:
            d += 1
        if d == 0:
            same += 1
        elif d <= rc:
            near.append((n, d, s))
        else:
            beyond += 1
    ordered = []
    pool = list(near)
    while pool:
        pick = pool[0]
        for r in pool[1:]:
            if (r[1], r[0]) < (pick[1], pick[0]):
                pick = r
        ordered.append(pick)
        pool.remove(pick)
    best = None
    for r in near:
        if best is None or (r[2], -r[1]) > (best[2], -best[1]) or (r[2], -r[1]) == (best[2], -best[1]) and r[0] < best[0]:
            best = r
    return {'near': ordered, 'near_total': sum(r[2] for r in near), 'taught_count': same,
            'beyond_count': beyond, 'best': best[0] if best else None}


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
    f = m.near_transfer_pick
    assert f([10], [('a', 11, 5)]) == {'near': [('a', 1, 5)], 'near_total': 5, 'taught_count': 0, 'beyond_count': 0, 'best': 'a'}
    assert f([10], [('a', 10, 5)]) == {'near': [], 'near_total': 0, 'taught_count': 1, 'beyond_count': 0, 'best': None}
    assert f([10], [('a', 13, 5)]) == {'near': [], 'near_total': 0, 'taught_count': 0, 'beyond_count': 1, 'best': None}
    # default reach 2: distance 2 in, 3 out; reach 1 and 3 and 10 move the edge
    assert [r[0] for r in f([10], [('a', 12, 1), ('b', 13, 1)])['near']] == ['a']
    assert [r[0] for r in f([10], [('a', 12, 1), ('b', 13, 1)], 1)['near']] == []
    assert [r[0] for r in f([10], [('a', 12, 1), ('b', 13, 1)], 3)['near']] == ['a', 'b']
    assert [r[0] for r in f([10], [('a', 9, 1), ('b', 20, 1), ('c', 21, 1)], 10)['near']] == ['a', 'b']
    assert f([10], [('a', 12, 1)]) == f([10], [('a', 12, 1)], 2)
    # both sides and nearest of several taught
    r = f([10, 30], [('a', 28, 3), ('b', 12, 7), ('c', 31, 2), ('d', 20, 9), ('e', 30, 9)])
    assert r == {'near': [('c', 1, 2), ('a', 2, 3), ('b', 2, 7)], 'near_total': 12, 'taught_count': 1, 'beyond_count': 1, 'best': 'b'}
    # ordering: closest first, ties by name
    r = f([10], [('z', 11, 1), ('b', 12, 1), ('a', 8, 1), ('c', 9, 1)])
    assert [x[0] for x in r['near']] == ['c', 'z', 'a', 'b']
    # best: highest score, then closer, then smaller name
    assert f([10], [('a', 12, 5), ('b', 11, 5)])['best'] == 'b'
    assert f([10], [('b', 12, 5), ('a', 8, 5)])['best'] == 'a'
    assert f([10], [('a', 11, 4), ('b', 12, 6)])['best'] == 'b'
    assert f([10], [('a', 11, 0)])['best'] == 'a'
    assert f([0, 50], [('a', 1, 1), ('b', 49, 2)])['near'] == [('a', 1, 1), ('b', 1, 2)]
    assert f((0, 50), (['a', 0, 1], ('b', 50, 2)))['taught_count'] == 2
    assert f([10], [('x' * 12, 11, 10)])['near'] == [('x' * 12, 1, 10)]
    assert f(list(range(0, 12, 2)), [(chr(97 + i), 1 + 2 * i, 1) for i in range(6)])['near_total'] == 6
    assert len(f([10], [(chr(97 + i), 11, 1) for i in range(8)])['near']) == 8
    rng = random.Random(836)
    for _ in range(800):
        td = rng.sample(range(0, 51), rng.randint(1, 6))
        ts = [(chr(97 + i), rng.randint(0, 50), rng.randint(0, 10)) for i in range(rng.randint(1, 8))]
        rc = rng.randint(1, 10)
        assert f(td, ts, rc) == _oracle(set(td), ts, rc), (td, ts, rc)
        assert f(td, ts) == _oracle(set(td), ts, 2)


def _late(m):
    f = m.near_transfer_pick
    RC = 'reach must be a nonbool integer between 1 and 10'
    TT = 'taught must be a list or tuple'
    TS = 'taught must contain 1 to 6 entries'
    TE = 'each taught position must be a nonbool integer between 0 and 50'
    TD = 'taught positions must be distinct'
    KT = 'tasks must be a list or tuple'
    KS = 'tasks must contain 1 to 8 entries'
    KE = 'each task must be a (name, position, score) tuple'
    NM = 'each name must be an ASCII string of 1 to 12 characters'
    PO = 'position must be a nonbool integer between 0 and 50'
    SC = 'score must be a nonbool integer between 0 and 10'
    ND = 'names must be distinct'
    ok = [('x', 1, 1)]
    badint = lambda lo, hi: (lo - 1, hi + 1, True, False, 1.0, '1', None, I(lo), LyingI(lo), LyingI(10 ** 30), I(10 ** 30))
    for bad in badint(1, 10):
        _raises(ValueError, RC, f, [1], ok, bad)
    f([1], ok, 1)
    f([1], ok, 10)
    for bad in ('ab', None, 5, {}, L([1]), T([1]), L(), T()):
        _raises(TypeError, TT, f, bad, ok)
    _raises(ValueError, TS, f, [], ok)
    _raises(ValueError, TS, f, list(range(7)), ok)
    for bad in badint(0, 50):
        _raises(ValueError, TE, f, [bad], ok)
        _raises(ValueError, TE, f, [1, bad], ok)
    f([0, 50], ok)
    _raises(ValueError, TD, f, [1, 1], ok)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, KT, f, [1], bad)
    _raises(ValueError, KS, f, [1], [])
    _raises(ValueError, KS, f, [1], [(chr(97 + i), 1, 1) for i in range(9)])
    for bad in ('ab', None, 5, ('x', 1), ('x', 1, 1, 1), (), {'x': 1}, L(['x', 1, 1]), T(('x', 1, 1))):
        _raises(ValueError, KE, f, [1], [bad])
        _raises(ValueError, KE, f, [1], [('y', 1, 1), bad])
    for bad in ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661'):
        _raises(ValueError, NM, f, [1], [(bad, 1, 1)])
        _raises(ValueError, NM, f, [1], [('y', 1, 1), (bad, 1, 1)])
    f([1], [('A~ z', 1, 1)])
    for bad in badint(0, 50):
        _raises(ValueError, PO, f, [1], [('x', bad, 1)])
        _raises(ValueError, PO, f, [1], [('y', 1, 1), ('x', bad, 1)])
    for bad in badint(0, 10):
        _raises(ValueError, SC, f, [1], [('x', 1, bad)])
        _raises(ValueError, SC, f, [1], [('y', 1, 1), ('x', 1, bad)])
    f([1], [('x', 0, 0)])
    f([1], [('x', 50, 10)])
    _raises(ValueError, ND, f, [1], [('x', 1, 1), ('x', 1, 1)])
    _raises(ValueError, RC, f, None, None, 0)
    _raises(TypeError, TT, f, None, None)
    _raises(ValueError, TS, f, [], None)
    _raises(ValueError, TE, f, [99, 99], None)
    _raises(ValueError, TD, f, [1, 1], None)
    _raises(TypeError, KT, f, [1], None)
    _raises(ValueError, KS, f, [1], [])
    _raises(ValueError, KE, f, [1], [1])
    _raises(ValueError, NM, f, [1], [(1, 99, 99)])
    _raises(ValueError, PO, f, [1], [('x', 99, 99)])
    _raises(ValueError, SC, f, [1], [('x', 1, 99), ('x', 1, 99)])
    _raises(ValueError, ND, f, [1], [('x', 1, 1), ('x', 1, 1)])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def _ints(var, lo, hi, tail=''):
    base = "type(%s) is not int or not %s <= %s <= %s" % (var, lo, var, hi)
    return [
        (base, "not isinstance(%s, int) or not %s <= %s <= %s" % (var, lo, var, hi)),
        (base, "isinstance(%s, bool) or not isinstance(%s, int) or not %s <= %s <= %s" % (var, var, lo, var, hi)),
        (base, "type(%s) is not int or not %s <= %s <= %s" % (var, lo - 1, var, hi)),
        (base, "type(%s) is not int or not %s <= %s <= %s" % (var, lo + 1, var, hi)),
        (base, "type(%s) is not int or not %s <= %s <= %s" % (var, lo, var, hi - 1)),
        (base, "type(%s) is not int or not %s <= %s <= %s" % (var, lo, var, hi + 1)),
    ]


MUTANTS = [
    ("reach=2", "reach=1"),
    ("reach=2", "reach=3"),
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
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "not isinstance(name, str) or not name.isascii() or not 1 <= len(name) <= 12"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "type(name) is not str or not 1 <= len(name) <= 12"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "type(name) is not str or not name.isalnum() or not 1 <= len(name) <= 12"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "type(name) is not str or not name.isascii() or not 0 <= len(name) <= 12"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "type(name) is not str or not name.isascii() or not 1 <= len(name) < 12"),
    ("type(name) is not str or not name.isascii() or not 1 <= len(name) <= 12", "type(name) is not str or not name.isascii() or not 1 <= len(name) <= 13"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("distance = min(abs(position - t) for t in taught)", "distance = abs(position - taught[0])"),
    ("distance = min(abs(position - t) for t in taught)", "distance = max(abs(position - t) for t in taught)"),
    ("distance = min(abs(position - t) for t in taught)", "distance = min(position - t for t in taught)"),
    ("if distance == 0:", "if distance <= 0 and False:"),
    ("elif distance <= reach:", "elif distance < reach:"),
    ("elif distance <= reach:", "elif distance <= reach + 1:"),
    ("same += 1", "same += 2"),
    ("beyond += 1", "beyond += 2"),
    ("near.sort(key=lambda r: (r[0], r[1]))", "near.sort(key=lambda r: (r[1], r[0]))"),
    ("near.sort(key=lambda r: (r[0], r[1]))", "near.sort(key=lambda r: (r[0], r[2]))"),
    ("near.sort(key=lambda r: (r[0], r[1]))", "near.sort(key=lambda r: (-r[0], r[1]))"),
    ("min(near, key=lambda r: (-r[2], r[0], r[1]))[1]", "min(near, key=lambda r: (r[2], r[0], r[1]))[1]"),
    ("min(near, key=lambda r: (-r[2], r[0], r[1]))[1]", "min(near, key=lambda r: (-r[2], -r[0], r[1]))[1]"),
    ("min(near, key=lambda r: (-r[2], r[0], r[1]))[1]", "min(near, key=lambda r: (-r[2], r[1], r[0]))[1]"),
    ("min(near, key=lambda r: (-r[2], r[0], r[1]))[1]", "min(near, key=lambda r: (-r[2], r[0], r[1]))[0]"),
    ("min(near, key=lambda r: (-r[2], r[0], r[1]))[1]", "max(near, key=lambda r: (r[2], -r[0], r[1]))[1]"),
    ("'near_total': sum(r[2] for r in near)", "'near_total': sum(r[2] for r in near[:1])"),
    ("'near_total': sum(r[2] for r in near)", "'near_total': sum(r[0] for r in near)"),
]
for _v, _lo, _hi in (('reach', 1, 10), ('t', 0, 50), ('position', 0, 50), ('score', 0, 10)):
    MUTANTS += _ints(_v, _lo, _hi)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
