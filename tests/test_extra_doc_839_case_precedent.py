import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import case_precedent as mod

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
    assert mod.SCOPE == 'PARTIAL: nearest-case vote over supplied numeric features, no precedent is judged'
    assert len(mod.NOT_CLAIMED) == 5 and 'precedent relevance' in mod.NOT_CLAIMED and 'real case-based reasoning' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Case-Based Reasoning - Uses precedents' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(cs, q, k):
    """Independent: repeated minimum extraction, then a tally by scanning outcomes in neighbour order."""
    left = [(sum(abs(f[i] - q[i]) for i in range(3)), cid, o) for cid, f, o in cs]
    order = []
    while left:
        best = left[0]
        for r in left[1:]:
            if r[0] < best[0] or (r[0] == best[0] and r[1] < best[1]):
                best = r
        order.append(best)
        left.remove(best)
    vot = order[:k]
    outs = [r[2] for r in vot]
    win, wv = None, 0
    for o in outs:
        n = outs.count(o)
        if n > wv:
            win, wv = o, n
    return {'precedent': order[0][1], 'distance': order[0][0], 'neighbours': [r[1] for r in vot],
            'outcome': win, 'votes': wv}


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
    f = m.case_precedent
    assert f([('a', (1, 2, 3), 'yes')], (1, 2, 3)) == {'precedent': 'a', 'distance': 0, 'neighbours': ['a'], 'outcome': 'yes', 'votes': 1}
    cs = [('a', (0, 0, 0), 'no'), ('b', (1, 1, 1), 'yes'), ('c', (2, 2, 2), 'yes'), ('d', (9, 9, 9), 'no')]
    q = (1, 1, 2)
    # k=1 follows the nearest case (b, distance 1); the default k=3 takes b, c, a and yes wins 2-1
    assert f(cs, q, 1) == {'precedent': 'b', 'distance': 1, 'neighbours': ['b'], 'outcome': 'yes', 'votes': 1}
    assert f(cs, q) == {'precedent': 'b', 'distance': 1, 'neighbours': ['b', 'c', 'a'], 'outcome': 'yes', 'votes': 2}
    assert f(cs, q) == f(cs, q, 3)
    assert f(cs, q, 2) == {'precedent': 'b', 'distance': 1, 'neighbours': ['b', 'c'], 'outcome': 'yes', 'votes': 2}
    assert f(cs, q, 4)['neighbours'] == ['b', 'c', 'a', 'd'] and f(cs, q, 5)['neighbours'] == ['b', 'c', 'a', 'd']
    assert f(cs, q, 4)['outcome'] == 'yes' and f(cs, q, 4)['votes'] == 2
    # a vote tie goes to the outcome whose nearest case comes first
    assert f(cs, q, 4)['outcome'] == 'yes'
    t = [('a', (0, 0, 0), 'x'), ('b', (1, 0, 0), 'y')]
    assert f(t, (0, 0, 0), 2) == {'precedent': 'a', 'distance': 0, 'neighbours': ['a', 'b'], 'outcome': 'x', 'votes': 1}
    assert f(t, (1, 0, 0), 2) == {'precedent': 'b', 'distance': 0, 'neighbours': ['b', 'a'], 'outcome': 'y', 'votes': 1}
    assert f(t, (1, 0, 0)) == f(t, (1, 0, 0), 2)
    # distance ties are broken by case_id, not input order
    u = [('z', (1, 0, 0), 'zz'), ('m', (0, 1, 0), 'mm')]
    assert f(u, (0, 0, 0), 1)['precedent'] == 'm' and f(u[::-1], (0, 0, 0), 1)['precedent'] == 'm'
    assert f(u, (0, 0, 0), 1)['distance'] == 1
    # a lone nearest outcome loses to two farther ones when k allows
    v = [('a', (0, 0, 0), 'p'), ('b', (5, 5, 5), 'q'), ('c', (5, 5, 6), 'q')]
    assert f(v, (0, 0, 0), 1)['outcome'] == 'p'
    assert f(v, (0, 0, 0), 3) == {'precedent': 'a', 'distance': 0, 'neighbours': ['a', 'b', 'c'], 'outcome': 'q', 'votes': 2}
    assert f(v, (0, 0, 0), 2)['outcome'] == 'p' and f(v, (0, 0, 0), 2)['votes'] == 1
    # manhattan, not squared or max: (3,0,0) is farther than (1,1,1) by sum, nearer by squared sum? 9 vs 3
    w = [('a', (3, 0, 0), 'n'), ('b', (2, 2, 2), 'f')]
    assert f(w, (0, 0, 0), 1)['precedent'] == 'a' and f(w, (0, 0, 0), 1)['distance'] == 3
    w2 = [('a', (2, 2, 0), 'n'), ('b', (3, 0, 0), 'f')]
    assert f(w2, (0, 0, 0), 1)['precedent'] == 'b'
    assert f([('a', [9, 0, 9], 'x' * 12), ('b', (0, 9, 0), 'y')], [9, 0, 9], 1)['outcome'] == 'x' * 12
    assert f([('a', (0, 0, 0), 'Q')], (9, 9, 9))['distance'] == 27
    assert len(f([(chr(97 + i), (i, 0, 0), 'o') for i in range(8)], (0, 0, 0), 5)['neighbours']) == 5
    rng = random.Random(839)
    for _ in range(1200):
        n = rng.randint(1, 8)
        cs2 = [(chr(97 + i), rng.choice((list, tuple))(rng.randint(0, 9) for _ in range(3)), rng.choice('pqr')) for i in range(n)]
        rng.shuffle(cs2)
        q2 = rng.choice((list, tuple))(rng.randint(0, 9) for _ in range(3))
        k2 = rng.randint(1, 5)
        assert f(cs2, q2, k2) == _oracle(cs2, q2, k2), (cs2, q2, k2)
        assert f(cs2, q2) == _oracle(cs2, q2, 3)


def _late(m):
    f = m.case_precedent
    KK = 'k must be a nonbool integer between 1 and 5'
    CT = 'cases must be a list or tuple'
    CS = 'cases must contain 1 to 8 entries'
    CE = 'each case must be a (case_id, features, outcome) tuple'
    ID = 'each case_id must be an ASCII string of 1 to 12 characters'
    FT = 'features must be a list or tuple'
    FS = 'features must contain 3 entries'
    FE = 'each feature must be a nonbool integer between 0 and 9'
    OU = 'each outcome must be an ASCII string of 1 to 12 characters'
    DI = 'case_ids must be distinct'
    QT = 'query must be a list or tuple'
    QS = 'query must contain 3 entries'
    QE = 'each query value must be a nonbool integer between 0 and 9'
    ok = [('a', (0, 0, 0), 'o')]
    q = (0, 0, 0)
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661')
    badint = (-1, 10, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30))
    for bad in (0, 6, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, KK, f, ok, q, bad)
    f(ok, q, 1)
    f(ok, q, 5)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, CT, f, bad, q)
    _raises(ValueError, CS, f, [], q)
    _raises(ValueError, CS, f, [(chr(97 + i), (0, 0, 0), 'o') for i in range(9)], q)
    f([(chr(97 + i), (0, 0, 0), 'o') for i in range(8)], q)
    for bad in ('ab', None, 5, ('a', (0, 0, 0)), ('a', (0, 0, 0), 'o', 1), (), {'a': 1}, L(['a', (0, 0, 0), 'o']), T(('a', (0, 0, 0), 'o'))):
        _raises(ValueError, CE, f, [bad], q)
        _raises(ValueError, CE, f, [('b', (0, 0, 0), 'o'), bad], q)
    for bad in names:
        _raises(ValueError, ID, f, [(bad, (0, 0, 0), 'o')], q)
        _raises(ValueError, ID, f, [('b', (0, 0, 0), 'o'), (bad, (0, 0, 0), 'o')], q)
        _raises(ValueError, OU, f, [('a', (0, 0, 0), bad)], q)
        _raises(ValueError, OU, f, [('b', (0, 0, 0), 'o'), ('a', (0, 0, 0), bad)], q)
    f([('A~ z', (0, 0, 0), 'A~ z')], q)
    for bad in ('ab', None, 5, {}, {0, 1, 2}, L((0, 0, 0)), T((0, 0, 0)), L(), T()):
        _raises(ValueError, FT, f, [('a', bad, 'o')], q)
        _raises(ValueError, FT, f, [('b', (0, 0, 0), 'o'), ('a', bad, 'o')], q)
    for bad in ((), (0,), (0, 0), (0, 0, 0, 0)):
        _raises(ValueError, FS, f, [('a', bad, 'o')], q)
        _raises(ValueError, FS, f, [('b', (0, 0, 0), 'o'), ('a', bad, 'o')], q)
    for bad in badint:
        _raises(ValueError, FE, f, [('a', (bad, 0, 0), 'o')], q)
        _raises(ValueError, FE, f, [('a', (0, 0, bad), 'o')], q)
        _raises(ValueError, FE, f, [('b', (0, 0, 0), 'o'), ('a', (0, bad, 0), 'o')], q)
        _raises(ValueError, QE, f, ok, (bad, 0, 0))
        _raises(ValueError, QE, f, ok, (0, 0, bad))
        _raises(ValueError, QE, f, ok, [0, bad, 0])
    f([('a', (9, 9, 9), 'o')], (9, 9, 9))
    _raises(ValueError, DI, f, [('a', (0, 0, 0), 'o'), ('a', (1, 1, 1), 'p')], q)
    for bad in ('ab', None, 5, {}, L(q), T(q), L(), T()):
        _raises(TypeError, QT, f, ok, bad)
    for bad in ((), (0,), (0, 0), (0, 0, 0, 0)):
        _raises(ValueError, QS, f, ok, bad)
    f(ok, [1, 2, 3])
    # validation order
    _raises(ValueError, KK, f, None, None, 0)
    _raises(TypeError, CT, f, None, None)
    _raises(ValueError, CS, f, [], None)
    _raises(ValueError, CE, f, [1], None)
    _raises(ValueError, ID, f, [(1, 5, 5)], None)
    _raises(ValueError, FT, f, [('a', 5, 5)], None)
    _raises(ValueError, FS, f, [('a', (), 5)], None)
    _raises(ValueError, FE, f, [('a', (99, 0, 0), 5)], None)
    _raises(ValueError, OU, f, [('a', (0, 0, 0), 5), ('a', (0, 0, 0), 5)], None)
    _raises(ValueError, DI, f, [('a', (0, 0, 0), 'o'), ('a', (0, 0, 0), 'o')], None)
    _raises(TypeError, QT, f, ok, None)
    _raises(ValueError, QS, f, ok, ())
    _raises(ValueError, QE, f, ok, (99, 0, 0))


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
    ("k=3", "k=2"),
    ("k=3", "k=4"),
    (LB, "isinstance(x, str) and x.isascii() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isalnum() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 0 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) < 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) <= 13"),
    ("type(cases) not in (list, tuple)", "not isinstance(cases, (list, tuple))"),
    ("not 1 <= len(cases) <= 8", "not 0 <= len(cases) <= 8"),
    ("not 1 <= len(cases) <= 8", "not 1 <= len(cases) < 8"),
    ("not 1 <= len(cases) <= 8", "not 1 <= len(cases) <= 9"),
    ("type(c) not in (list, tuple) or len(c) != 3", "not isinstance(c, (list, tuple)) or len(c) != 3"),
    ("type(c) not in (list, tuple) or len(c) != 3", "type(c) not in (list, tuple) or len(c) > 3"),
    ("type(c) not in (list, tuple) or len(c) != 3", "type(c) not in (list, tuple) or len(c) < 3"),
    ("type(feats) not in (list, tuple)", "not isinstance(feats, (list, tuple))"),
    ("if len(feats) != 3:", "if len(feats) > 3:"),
    ("if len(feats) != 3:", "if len(feats) < 3:"),
    ("rows.append((cid, tuple(feats), outcome))", "rows.append((cid, tuple(feats[:2]) + (0,), outcome))"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("type(query) not in (list, tuple)", "not isinstance(query, (list, tuple))"),
    ("if len(query) != 3:", "if len(query) > 3:"),
    ("if len(query) != 3:", "if len(query) < 3:"),
    ("sum(abs(a - b) for a, b in zip(f, query))", "sum((a - b) ** 2 for a, b in zip(f, query))"),
    ("sum(abs(a - b) for a, b in zip(f, query))", "max(abs(a - b) for a, b in zip(f, query))"),
    ("sum(abs(a - b) for a, b in zip(f, query))", "sum(a - b for a, b in zip(f, query))"),
    ("sum(abs(a - b) for a, b in zip(f, query))", "sum(abs(a - b) for a, b in zip(f[:2], query[:2]))"),
    ("voters = ranked[:k]", "voters = ranked[:k + 1]"),
    ("voters = ranked[:k]", "voters = ranked[:k - 1]"),
    ("voters = ranked[:k]", "voters = ranked[1:k + 1]"),
    ("votes[o] = votes.get(o, 0) + 1", "votes[o] = 1"),
    ("top = max(votes.values())", "top = min(votes.values())"),
    ("winner = next(o for _, _, o in voters if votes[o] == top)", "winner = next(o for _, _, o in reversed(voters) if votes[o] == top)"),
    ("winner = next(o for _, _, o in voters if votes[o] == top)", "winner = min(o for _, _, o in voters if votes[o] == top)"),
    ("winner = next(o for _, _, o in voters if votes[o] == top)", "winner = voters[0][2]"),
    ("'precedent': ranked[0][1]", "'precedent': ranked[-1][1]"),
    ("'distance': ranked[0][0]", "'distance': ranked[-1][0]"),
    ("'neighbours': [cid for _, cid, _ in voters]", "'neighbours': sorted(cid for _, cid, _ in voters)"),
    ("'votes': top", "'votes': len(voters)"),
]
for _v, _lo, _hi in (('k', 1, 5), ('x', 0, 9)):
    MUTANTS += _ints(_v, _lo, _hi)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
