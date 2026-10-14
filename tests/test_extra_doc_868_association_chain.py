import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import association_chain as mod

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
    assert mod.SCOPE == 'PARTIAL: greedy strongest-link walk over supplied weighted links, no association is thought'
    assert len(mod.NOT_CLAIMED) == 5 and 'meaning of the links' in mod.NOT_CLAIMED and 'free association' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Associative Thinking - Connects concepts' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(ls, st, sp):
    """Independent: rescan the whole link list at every step, with a seen list and a best-so-far scan."""
    chain = [st]
    taken = []
    for _ in range(sp):
        here = chain[-1]
        best = None
        for a, b, s in ls:
            for x, y in ((a, b), (b, a)):
                if x == here and y not in chain:
                    if best is None or s > best[1] or (s == best[1] and y < best[0]):
                        best = (y, s)
        if best is None:
            break
        chain.append(best[0])
        taken.append(best[1])
    return {'chain': chain, 'strengths': taken, 'total': sum(taken), 'stopped': len(taken) < sp}


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
    f = m.association_chain
    assert f([('a', 'b', 5)], 'a') == {'chain': ['a', 'b'], 'strengths': [5], 'total': 5, 'stopped': True}
    assert f([('a', 'b', 5)], 'b') == {'chain': ['b', 'a'], 'strengths': [5], 'total': 5, 'stopped': True}
    assert f([('a', 'b', 5), ('b', 'c', 4), ('c', 'd', 3)], 'a') == {'chain': ['a', 'b', 'c', 'd'], 'strengths': [5, 4, 3], 'total': 12, 'stopped': False}
    # default steps 3: a fourth hop is not taken; 1, 2, 4 and 6 move the edge
    ch = [('a', 'b', 1), ('b', 'c', 1), ('c', 'd', 1), ('d', 'e', 1), ('e', 'f', 1), ('f', 'g', 1), ('g', 'h', 1)]
    assert f(ch, 'a')['chain'] == list('abcd') and f(ch, 'a') == f(ch, 'a', 3)
    assert f(ch, 'a', 1)['chain'] == list('ab') and f(ch, 'a', 2)['chain'] == list('abc')
    assert f(ch, 'a', 4)['chain'] == list('abcde') and f(ch, 'a', 6) == {'chain': list('abcdefg'), 'strengths': [1] * 6, 'total': 6, 'stopped': False}
    assert f(ch, 'a', 3)['stopped'] is False and f([('a', 'b', 1)], 'a', 2)['stopped'] is True and f(ch, 'h', 1)['stopped'] is False
    # strongest link wins over input order, ties go to the smaller name
    assert f([('a', 'z', 3), ('a', 'b', 9), ('a', 'c', 4)], 'a', 1)['chain'] == ['a', 'b']
    assert f([('a', 'z', 3), ('a', 'c', 3), ('a', 'm', 3)], 'a', 1)['chain'] == ['a', 'c']
    assert f([('a', 'z', 3), ('a', 'c', 3), ('a', 'm', 3)][::-1], 'a', 1)['chain'] == ['a', 'c']
    assert f([('a', 'b', 2), ('a', 'c', 7)], 'a', 1)['strengths'] == [7]
    # concepts already in the chain are skipped, so the walk never loops
    assert f([('a', 'b', 9), ('b', 'c', 8), ('c', 'a', 7)], 'a') == {'chain': ['a', 'b', 'c'], 'strengths': [9, 8], 'total': 17, 'stopped': True}
    assert f([('a', 'b', 9), ('b', 'c', 1), ('b', 'd', 5), ('c', 'a', 8)], 'a', 3) == {'chain': ['a', 'b', 'd'], 'strengths': [9, 5], 'total': 14, 'stopped': True}
    assert f([('a', 'b', 5), ('a', 'c', 5), ('c', 'd', 9)], 'a', 2) == {'chain': ['a', 'b'], 'strengths': [5], 'total': 5, 'stopped': True}
    # greedy, not best total: a strong first hop can lead to a weak path
    assert f([('s', 'x', 9), ('x', 'y', 1), ('s', 'z', 8), ('z', 'w', 8)], 's', 2)['total'] == 10
    # mixed list and tuple links, in both orders
    base = f([('a', 'b', 5), ('b', 'c', 4)], 'a')
    assert f([('a', 'b', 5), ['b', 'c', 4]], 'a') == base
    assert f([['a', 'b', 5], ('b', 'c', 4)], 'a') == base
    assert f((['a', 'b', 5], ['b', 'c', 4]), 'a') == base
    assert f([('x' * 12, 'A~ z', 9)], 'A~ z')['chain'] == ['A~ z', 'x' * 12]
    assert f([('A', 'a', 1)], 'A')['chain'] == ['A', 'a']
    k8 = [(x, y, 1) for i, x in enumerate('abcd') for y in 'abcd'[i + 1:]]
    assert f(k8, 'a', 6)['chain'] == list('abcd')
    rng = random.Random(868)
    pool = 'abcdefgh'
    for _ in range(1500):
        nodes = rng.sample(pool, rng.randint(2, 8))
        allp = [(x, y) for i, x in enumerate(nodes) for y in nodes[i + 1:]]
        es = [(x, y, rng.randint(1, 9)) for x, y in rng.sample(allp, rng.randint(1, min(10, len(allp))))]
        es = [rng.choice((list, tuple))((a, b, s) if rng.random() < .5 else (b, a, s)) for a, b, s in es]
        named = sorted({n for e in es for n in e[:2]})
        st = rng.choice(named)
        sp = rng.randint(1, 6)
        assert f(es, st, sp) == _oracle(es, st, sp), (es, st, sp)
        assert f(es, st) == _oracle(es, st, 3)


def _late(m):
    f = m.association_chain
    SP = 'steps must be a nonbool integer between 1 and 6'
    LT = 'links must be a list or tuple'
    LS = 'links must contain 1 to 10 entries'
    LE = 'each link must be an (a, b, strength) tuple'
    FA = 'each first concept must be a printable ASCII string of 1 to 12 characters'
    SB = 'each second concept must be a printable ASCII string of 1 to 12 characters'
    SR = 'strength must be a nonbool integer between 1 and 9'
    DF = 'the concepts of a link must differ'
    DI = 'links must be distinct'
    NN = 'links must name at most 8 concepts'
    ST = 'start must be a printable ASCII string of 1 to 12 characters'
    SN = 'start must be named in links'
    ok = [('a', 'b', 1), ('b', 'c', 1)]
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661',
             '\n', 'a\n', '\ta', 'a\x00', '\x7f', 'a\r', '\x1b[0m', 'a\x0b')
    for bad in (0, 7, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, SP, f, ok, 'a', bad)
    f(ok, 'a', 1)
    f(ok, 'a', 6)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, LT, f, bad, 'a')
    _raises(ValueError, LS, f, [], 'a')
    six = [(x, y, 1) for i, x in enumerate('abcdef') for y in 'abcdef'[i + 1:]]
    _raises(ValueError, LS, f, six[:11], 'a')
    f(six[:10], 'a')
    for bad in ('ab', None, 5, ('a', 'b'), ('a', 'b', 1, 1), (), {'a': 1}, L(['a', 'b', 1]), T(('a', 'b', 1))):
        _raises(ValueError, LE, f, [bad], 'a')
        _raises(ValueError, LE, f, [('a', 'b', 1), bad], 'a')
    for bad in names:
        _raises(ValueError, FA, f, [(bad, 'b', 1)], 'a')
        _raises(ValueError, FA, f, [('a', 'b', 1), (bad, 'c', 1)], 'a')
        _raises(ValueError, SB, f, [('a', bad, 1)], 'a')
        _raises(ValueError, SB, f, [('a', 'b', 1), ('b', bad, 1)], 'a')
        _raises(ValueError, ST, f, ok, bad)
    f([(' ', 'A~ z', 1)], ' ')
    for bad in (0, 10, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, SR, f, [('a', 'b', bad)], 'a')
        _raises(ValueError, SR, f, [('a', 'b', 1), ('b', 'c', bad)], 'a')
    f([('a', 'b', 9)], 'a')
    _raises(ValueError, DF, f, [('a', 'a', 1)], 'a')
    _raises(ValueError, DF, f, [('a', 'b', 1), ('c', 'c', 1)], 'a')
    _raises(ValueError, DI, f, [('a', 'b', 1), ('a', 'b', 2)], 'a')
    _raises(ValueError, DI, f, [('a', 'b', 1), ('b', 'a', 1)], 'a')
    _raises(ValueError, DI, f, [('a', 'b', 1), ['b', 'a', 1]], 'a')
    _raises(ValueError, DI, f, [['a', 'b', 1], ('b', 'a', 1)], 'a')
    nine = [(chr(97 + i), chr(98 + i), 1) for i in range(8)]
    _raises(ValueError, NN, f, nine, 'a')
    f(nine[:7], 'a')
    _raises(ValueError, SN, f, ok, 'z')
    _raises(ValueError, SN, f, ok, 'A')
    # validation order
    _raises(ValueError, SP, f, None, None, 0)
    _raises(TypeError, LT, f, None, None)
    _raises(ValueError, LS, f, [], None)
    _raises(ValueError, LE, f, [1], None)
    _raises(ValueError, FA, f, [(1, 1, 1)], None)
    _raises(ValueError, SB, f, [('a', 1, 1)], None)
    _raises(ValueError, SR, f, [('a', 'b', 0), ('a', 'a', 1)], None)
    _raises(ValueError, DF, f, [('a', 'a', 1), ('a', 'a', 1)], None)
    _raises(ValueError, DI, f, [('a', 'b', 1), ('a', 'b', 1)] , None)
    _raises(ValueError, NN, f, nine, None)
    _raises(ValueError, ST, f, ok, None)
    _raises(ValueError, SN, f, ok, 'zz')


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
    ("steps=3", "steps=2"),
    ("steps=3", "steps=4"),
    (LB, "isinstance(x, str) and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isalnum() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 0 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) < 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 13"),
    ("type(links) not in (list, tuple)", "not isinstance(links, (list, tuple))"),
    ("not 1 <= len(links) <= 10", "not 0 <= len(links) <= 10"),
    ("not 1 <= len(links) <= 10", "not 1 <= len(links) < 10"),
    ("not 1 <= len(links) <= 10", "not 1 <= len(links) <= 11"),
    ("type(e) not in (list, tuple) or len(e) != 3", "not isinstance(e, (list, tuple)) or len(e) != 3"),
    ("type(e) not in (list, tuple) or len(e) != 3", "type(e) not in (list, tuple) or len(e) > 3"),
    ("type(e) not in (list, tuple) or len(e) != 3", "type(e) not in (list, tuple) or len(e) < 3"),
    ("        if a == b:\n            raise", "        if False:\n            raise"),
    ("len({frozenset(r[:2]) for r in rows}) != len(rows)", "len({tuple(r[:2]) for r in rows}) != len(rows)"),
    ("len({frozenset(r[:2]) for r in rows}) != len(rows)", "False"),
    ("near.setdefault(a, []).append((b, strength))", "pass"),
    ("near.setdefault(b, []).append((a, strength))", "pass"),
    ("if len(near) > 8:", "if len(near) > 9:"),
    ("if len(near) > 8:", "if len(near) >= 8:"),
    ("if start not in near:", "if False:"),
    ("options = [(-s, n) for n, s in near[chain[-1]] if n not in chain]", "options = [(-s, n) for n, s in near[chain[-1]]]"),
    ("options = [(-s, n) for n, s in near[chain[-1]] if n not in chain]", "options = [(-s, n) for n, s in near[start] if n not in chain]"),
    ("options = [(-s, n) for n, s in near[chain[-1]] if n not in chain]", "options = [(s, n) for n, s in near[chain[-1]] if n not in chain]"),
    ("options = [(-s, n) for n, s in near[chain[-1]] if n not in chain]", "options = [(-s, n) for n, s in near[chain[-1]] if n != chain[-1]]"),
    ("s, n = min(options)", "s, n = max(options)"),
    ("s, n = min(options)", "s, n = min(options, key=lambda o: o[1])"),
    ("s, n = min(options)", "s, n = min(options, key=lambda o: (o[0], -ord(o[1][0])))"),
    ("taken.append(-s)", "taken.append(s)"),
    ("for _ in range(steps):", "for _ in range(steps - 1):"),
    ("for _ in range(steps):", "for _ in range(steps + 1):"),
    ("'total': sum(taken)", "'total': max(taken, default=0)"),
    ("'stopped': len(taken) < steps", "'stopped': len(taken) <= steps"),
    ("'stopped': len(taken) < steps", "'stopped': not taken"),
]
for _v, _lo, _hi in (('steps', 1, 6), ('strength', 1, 9)):
    MUTANTS += _ints(_v, _lo, _hi)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
