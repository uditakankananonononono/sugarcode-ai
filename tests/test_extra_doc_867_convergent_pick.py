import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import convergent_pick as mod

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
    assert mod.SCOPE == 'PARTIAL: staged elimination of supplied options by supplied weights, no thinking is assessed'
    assert len(mod.NOT_CLAIMED) == 5 and 'fitness of the criteria' in mod.NOT_CLAIMED and 'learner judgement' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Convergent Thinking - Narrows to best' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(op, wt, sl):
    """Independent: criteria order by repeated selection, survivors tracked as a set of names looked up in a dict."""
    sc = {n: list(s) for n, s in op}
    names = [n for n, _ in op]
    left = [0, 1, 2]
    order = []
    while left:
        pick = left[0]
        for c in left[1:]:
            if wt[c] > wt[pick]:
                pick = c
        order.append(pick)
        left.remove(pick)
    live = set(names)
    rounds = []
    for c in order:
        top = max(sc[n][c] for n in live)
        live = {n for n in live if sc[n][c] + sl >= top}
        rounds.append([n for n in names if n in live])
    fin = [n for n in names if n in live]
    tot = [(n, wt[0] * sc[n][0] + wt[1] * sc[n][1] + wt[2] * sc[n][2]) for n in fin]
    win = None
    for n, t in tot:
        if win is None or t > win[1] or (t == win[1] and n < win[0]):
            win = (n, t)
    return {'order': order, 'rounds': rounds, 'finalists': fin, 'totals': tot, 'winner': win[0]}


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
    f = m.convergent_pick
    r = f([('a', (5, 5, 5)), ('b', (5, 5, 5))], (1, 1, 1))
    assert r == {'order': [0, 1, 2], 'rounds': [['a', 'b']] * 3, 'finalists': ['a', 'b'], 'totals': [('a', 15), ('b', 15)], 'winner': 'a'}
    assert f([('b', (5, 5, 5)), ('a', (5, 5, 5))], (1, 1, 1))['winner'] == 'a'
    # criteria go heaviest first, ties by position
    assert f([('a', (1, 1, 1)), ('b', (1, 1, 1))], (2, 5, 2))['order'] == [1, 0, 2]
    assert f([('a', (1, 1, 1)), ('b', (1, 1, 1))], (1, 2, 3))['order'] == [2, 1, 0]
    assert f([('a', (1, 1, 1)), ('b', (1, 1, 1))], (3, 3, 3))['order'] == [0, 1, 2]
    # default slack 1: a score 1 below the best stays, 2 below goes; slack 0 and 2 move the edge
    ops = [('a', (10, 0, 0)), ('b', (9, 0, 0)), ('c', (8, 0, 0))]
    assert f(ops, (5, 1, 1))['rounds'][0] == ['a', 'b']
    assert f(ops, (5, 1, 1)) == f(ops, (5, 1, 1), 1)
    assert f(ops, (5, 1, 1), 0)['rounds'][0] == ['a'] and f(ops, (5, 1, 1), 2)['rounds'][0] == ['a', 'b', 'c']
    assert f(ops, (5, 1, 1), 5)['rounds'][0] == ['a', 'b', 'c']
    ops = [('a', (10, 0, 0)), ('b', (5, 0, 0))]
    assert f(ops, (5, 1, 1), 4)['rounds'][0] == ['a'] and f(ops, (5, 1, 1), 5)['rounds'][0] == ['a', 'b']
    # elimination order matters: the heavy criterion prunes before the light one is looked at
    ops = [('a', (10, 0, 10)), ('b', (4, 10, 4)), ('c', (9, 3, 9))]
    r = f(ops, (5, 1, 3), 1)
    assert r['order'] == [0, 2, 1] and r['rounds'] == [['a', 'c'], ['a', 'c'], ['c']]
    assert r['finalists'] == ['c'] and r['totals'] == [('c', 5 * 9 + 1 * 3 + 3 * 9)] and r['winner'] == 'c'
    # the final choice is by weighted total among finalists, ties to the smaller name
    ops = [('z', (10, 10, 0)), ('m', (10, 10, 1)), ('k', (10, 9, 2))]
    r = f(ops, (1, 1, 1), 3)
    assert r['finalists'] == ['z', 'm', 'k'] and r['totals'] == [('z', 20), ('m', 21), ('k', 21)] and r['winner'] == 'k'
    assert f(ops[::-1], (1, 1, 1), 3)['winner'] == 'k' and f(ops[::-1], (1, 1, 1), 3)['finalists'] == ['k', 'm', 'z']
    assert f([('a', (0, 0, 0)), ('b', (0, 0, 1))], (1, 1, 5), 0)['finalists'] == ['b']
    assert f([('a', (0, 0, 0)), ('b', (0, 1, 0))], (1, 5, 1), 0)['finalists'] == ['b']
    assert f([('a', (0, 0, 0)), ('b', (1, 0, 0))], (5, 1, 1), 0)['finalists'] == ['b']
    # mixed list and tuple options and scores, in both orders
    base = f([('a', (3, 4, 5)), ('b', (5, 4, 3))], (1, 2, 3))
    assert f([('a', [3, 4, 5]), ['b', (5, 4, 3)]], (1, 2, 3)) == base
    assert f([['a', (3, 4, 5)], ('b', [5, 4, 3])], [1, 2, 3]) == base
    assert f((['a', [3, 4, 5]], ('b', (5, 4, 3))), (1, 2, 3)) == base
    assert f([('x' * 12, (0, 0, 0)), ('A~ z', (10, 10, 10))], (1, 1, 1))['winner'] == 'A~ z'
    assert len(f([(chr(97 + i), (i, i, i)) for i in range(8)], (1, 1, 1), 5)['rounds'][0]) == 6
    rng = random.Random(867)
    for _ in range(1500):
        n = rng.randint(2, 8)
        op = [(chr(97 + i), [rng.randint(0, 10) for _ in range(3)]) for i in range(n)]
        rng.shuffle(op)
        wt = [rng.randint(1, 5) for _ in range(3)]
        sl = rng.randint(0, 5)
        op = [(a, rng.choice((list, tuple))(s)) if rng.random() < .5 else [a, rng.choice((list, tuple))(s)] for a, s in op]
        wt = rng.choice((list, tuple))(wt)
        assert f(op, wt, sl) == _oracle(op, wt, sl), (op, wt, sl)
        assert f(op, wt) == _oracle(op, wt, 1)


def _late(m):
    f = m.convergent_pick
    SL = 'slack must be a nonbool integer between 0 and 5'
    WT = 'weights must be a list or tuple'
    WS = 'weights must contain 3 entries'
    WE = 'each weight must be a nonbool integer between 1 and 5'
    OT = 'options must be a list or tuple'
    OS = 'options must contain 2 to 8 entries'
    OE = 'each option must be a (name, scores) tuple'
    NM = 'each name must be a printable ASCII string of 1 to 12 characters'
    CT = 'scores must be a list or tuple'
    CS = 'scores must contain 3 entries'
    CE = 'each score must be a nonbool integer between 0 and 10'
    ND = 'names must be distinct'
    ok = [('a', (1, 1, 1)), ('b', (2, 2, 2))]
    w = (1, 1, 1)
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661',
             '\n', 'a\n', '\ta', 'a\x00', '\x7f', 'a\r', '\x1b[0m', 'a\x0b')
    badint = lambda lo, hi: (lo - 1, hi + 1, True, False, 1.0, '1', None, I(lo), LyingI(lo), LyingI(10 ** 30), I(10 ** 30))
    for bad in badint(0, 5):
        _raises(ValueError, SL, f, ok, w, bad)
    f(ok, w, 0)
    f(ok, w, 5)
    for bad in ('ab', None, 5, {}, L(w), T(w), L(), T()):
        _raises(TypeError, WT, f, ok, bad)
    for bad in ((), (1,), (1, 1), (1, 1, 1, 1)):
        _raises(ValueError, WS, f, ok, bad)
    for bad in badint(1, 5):
        _raises(ValueError, WE, f, ok, (bad, 1, 1))
        _raises(ValueError, WE, f, ok, (1, 1, bad))
        _raises(ValueError, WE, f, ok, [1, bad, 1])
    f(ok, (5, 5, 5))
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, OT, f, bad, w)
    _raises(ValueError, OS, f, [('a', (1, 1, 1))], w)
    _raises(ValueError, OS, f, [], w)
    _raises(ValueError, OS, f, [(chr(97 + i), (1, 1, 1)) for i in range(9)], w)
    f([(chr(97 + i), (1, 1, 1)) for i in range(8)], w)
    for bad in ('ab', None, 5, ('a',), ('a', (1, 1, 1), 1), (), {'a': 1}, L(['a', (1, 1, 1)]), T(('a', (1, 1, 1)))):
        _raises(ValueError, OE, f, [bad, ('b', (1, 1, 1))], w)
        _raises(ValueError, OE, f, [('b', (1, 1, 1)), bad], w)
    for bad in names:
        _raises(ValueError, NM, f, [(bad, (1, 1, 1)), ('b', (1, 1, 1))], w)
        _raises(ValueError, NM, f, [('b', (1, 1, 1)), (bad, (1, 1, 1))], w)
    f([('A~ z', (1, 1, 1)), (' ', (1, 1, 1))], w)
    for bad in ('ab', None, 5, {}, {1, 2, 3}, L((1, 1, 1)), T((1, 1, 1)), L(), T()):
        _raises(ValueError, CT, f, [('a', bad), ('b', (1, 1, 1))], w)
        _raises(ValueError, CT, f, [('b', (1, 1, 1)), ('a', bad)], w)
    for bad in ((), (1,), (1, 1), (1, 1, 1, 1)):
        _raises(ValueError, CS, f, [('a', bad), ('b', (1, 1, 1))], w)
        _raises(ValueError, CS, f, [('b', (1, 1, 1)), ('a', bad)], w)
    for bad in badint(0, 10):
        _raises(ValueError, CE, f, [('a', (bad, 1, 1)), ('b', (1, 1, 1))], w)
        _raises(ValueError, CE, f, [('a', (1, 1, bad)), ('b', (1, 1, 1))], w)
        _raises(ValueError, CE, f, [('b', (1, 1, 1)), ('a', [1, bad, 1])], w)
    f([('a', (0, 0, 0)), ('b', (10, 10, 10))], w, 5)
    _raises(ValueError, ND, f, [('a', (1, 1, 1)), ('a', (2, 2, 2))], w)
    _raises(ValueError, SL, f, None, None, 6)
    _raises(TypeError, WT, f, None, None)
    _raises(ValueError, WS, f, None, ())
    _raises(ValueError, WE, f, None, (0, 0, 0))
    _raises(TypeError, OT, f, None, w)
    _raises(ValueError, OS, f, [], w)
    _raises(ValueError, OE, f, [1, 2], w)
    _raises(ValueError, NM, f, [(1, 5), ('b', 5)], w)
    _raises(ValueError, CT, f, [('a', 5), ('b', 5)], w)
    _raises(ValueError, CS, f, [('a', ()), ('b', ())], w)
    _raises(ValueError, CE, f, [('a', (99, 0, 0)), ('a', (99, 0, 0))], w)
    _raises(ValueError, ND, f, [('a', (1, 1, 1)), ('a', (2, 2, 2))], w)


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
    ("slack=1", "slack=0"),
    ("slack=1", "slack=2"),
    (LB, "isinstance(x, str) and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isalnum() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 0 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) < 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 13"),
    ("type(weights) not in (list, tuple)", "not isinstance(weights, (list, tuple))"),
    ("if len(weights) != 3:", "if len(weights) > 3:"),
    ("if len(weights) != 3:", "if len(weights) < 3:"),
    ("type(options) not in (list, tuple)", "not isinstance(options, (list, tuple))"),
    ("not 2 <= len(options) <= 8", "not 1 <= len(options) <= 8"),
    ("not 2 <= len(options) <= 8", "not 3 <= len(options) <= 8"),
    ("not 2 <= len(options) <= 8", "not 2 <= len(options) < 8"),
    ("not 2 <= len(options) <= 8", "not 2 <= len(options) <= 9"),
    ("type(o) not in (list, tuple) or len(o) != 2", "not isinstance(o, (list, tuple)) or len(o) != 2"),
    ("type(o) not in (list, tuple) or len(o) != 2", "type(o) not in (list, tuple) or len(o) > 2"),
    ("type(o) not in (list, tuple) or len(o) != 2", "type(o) not in (list, tuple) or len(o) < 2"),
    ("type(scores) not in (list, tuple)", "not isinstance(scores, (list, tuple))"),
    ("if len(scores) != 3:", "if len(scores) > 3:"),
    ("if len(scores) != 3:", "if len(scores) < 3:"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("key=lambda c: (-weights[c], c)", "key=lambda c: (weights[c], c)"),
    ("key=lambda c: (-weights[c], c)", "key=lambda c: (-weights[c], -c)"),
    ("key=lambda c: (-weights[c], c)", "key=lambda c: c"),
    ("best = max(r[1][c] for r in alive)", "best = min(r[1][c] for r in alive)"),
    ("best = max(r[1][c] for r in alive)", "best = max(r[1][c] for r in rows)"),
    ("if best - r[1][c] <= slack]", "if best - r[1][c] < slack]"),
    ("if best - r[1][c] <= slack]", "if best - r[1][c] <= slack + 1]"),
    ("alive = [r for r in alive if", "alive = [r for r in rows if"),
    ("rounds.append([r[0] for r in alive])", "rounds.append(sorted(r[0] for r in alive))"),
    ("zip(weights, sc)", "zip(weights, sc[::-1])"),
    ("sum(w * s for w, s in zip(weights, sc))", "sum(s for w, s in zip(weights, sc))"),
    ("min(totals, key=lambda t: (-t[1], t[0]))", "min(totals, key=lambda t: (t[1], t[0]))"),
    ("min(totals, key=lambda t: (-t[1], t[0]))", "min(totals, key=lambda t: (-t[1], -ord(t[0][0])))"),
    ("min(totals, key=lambda t: (-t[1], t[0]))", "min(totals, key=lambda t: -t[1])"),
    ("'order': order", "'order': sorted(order)"),
]
for _v, _lo, _hi in (('slack', 0, 5), ('w', 1, 5), ('s', 0, 10)):
    MUTANTS += _ints(_v, _lo, _hi)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
