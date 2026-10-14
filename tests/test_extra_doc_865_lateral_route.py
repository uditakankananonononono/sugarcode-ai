import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import lateral_route as mod

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
    assert mod.SCOPE == 'PARTIAL: shortest way around a direct link in a supplied small graph, no thinking is assessed'
    assert len(mod.NOT_CLAIMED) == 5 and 'creativity of the detour' in mod.NOT_CLAIMED and 'weighted or directed routes' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Lateral Thinking - Approaches indirectly' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(es, s, g):
    """Independent: enumerate every simple path by depth-first search and keep the smallest (length, node list)."""
    pairs = [tuple(sorted(e)) for e in es]
    direct = tuple(sorted((s, g))) in pairs
    use = [p for p in pairs if p != tuple(sorted((s, g)))]
    found = []

    def go(path):
        here = path[-1]
        if here == g:
            found.append(list(path))
            return
        for a, b in use:
            for x, y in ((a, b), (b, a)):
                if x == here and y not in path:
                    go(path + [y])

    go([s])
    if not found:
        return {'direct': direct, 'path': None, 'hops': None, 'detour': None}
    best = min(found, key=lambda p: (len(p), p))
    return {'direct': direct, 'path': best, 'hops': len(best) - 1, 'detour': len(best) - 2}


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
    f = m.lateral_route
    assert f([('a', 'b')], 'a', 'b') == {'direct': True, 'path': None, 'hops': None, 'detour': None}
    assert f([('a', 'b'), ('a', 'c')], 'a', 'b') == {'direct': True, 'path': None, 'hops': None, 'detour': None}
    assert f([('a', 'b'), ('a', 'c'), ('c', 'b')], 'a', 'b') == {'direct': True, 'path': ['a', 'c', 'b'], 'hops': 2, 'detour': 1}
    assert f([('a', 'c'), ('c', 'b')], 'a', 'b') == {'direct': False, 'path': ['a', 'c', 'b'], 'hops': 2, 'detour': 1}
    # reversed ends and reversed edge direction
    assert f([('c', 'a'), ('b', 'c')], 'b', 'a') == {'direct': False, 'path': ['b', 'c', 'a'], 'hops': 2, 'detour': 1}
    assert f([('b', 'a'), ('c', 'a'), ('b', 'c')], 'a', 'b')['direct'] is True
    # shortest wins over a smaller first step that leads to a longer route
    es = [('a', 'b'), ('a', 'c'), ('c', 'e'), ('e', 'b'), ('a', 'd'), ('d', 'b')]
    assert f(es, 'a', 'b') == {'direct': True, 'path': ['a', 'd', 'b'], 'hops': 2, 'detour': 1}
    # ties between shortest ways go to the smallest node list
    es = [('a', 'b'), ('a', 'd'), ('d', 'b'), ('a', 'c'), ('c', 'b')]
    assert f(es, 'a', 'b')['path'] == ['a', 'c', 'b'] and f(es[::-1], 'a', 'b')['path'] == ['a', 'c', 'b']
    es = [('s', 'g'), ('s', 'x'), ('s', 'y'), ('x', 'p'), ('y', 'p'), ('p', 'g'), ('x', 'q'), ('y', 'q'), ('q', 'g')]
    assert f(es, 's', 'g')['path'] == ['s', 'x', 'p', 'g']
    assert f(es, 'g', 's')['path'] == ['g', 'p', 'x', 's']
    assert f(es, 's', 'g')['hops'] == 3 and f(es, 's', 'g')['detour'] == 2
    # the direct link is never used even when it is the only short way
    assert f([('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')], 'a', 'b')['path'] == ['a', 'd', 'c', 'b']
    # disconnected without the direct link
    assert f([('a', 'b'), ('c', 'd')], 'a', 'c') == {'direct': False, 'path': None, 'hops': None, 'detour': None}
    assert f([('a', 'b'), ('c', 'd')], 'a', 'c')['direct'] is False
    # mixed list and tuple edges, in both orders
    assert f([('a', 'c'), ['c', 'b']], 'a', 'b')['path'] == ['a', 'c', 'b']
    assert f([['a', 'c'], ('c', 'b')], 'a', 'b')['path'] == ['a', 'c', 'b']
    assert f((['a', 'b'], ('a', 'c'), ['c', 'b']), 'a', 'b')['direct'] is True
    assert f([('x' * 12, 'y'), ('y', 'A~ z')], 'x' * 12, 'A~ z')['path'] == ['x' * 12, 'y', 'A~ z']
    assert f([('A', 'a'), ('a', 'b')], 'A', 'b')['path'] == ['A', 'a', 'b']
    chain = [(chr(97 + i), chr(98 + i)) for i in range(7)]
    assert f(chain, 'a', 'h') == {'direct': False, 'path': list('abcdefgh'), 'hops': 7, 'detour': 6}
    assert f([('a', 'b'), ('a', 'c'), ('a', 'd'), ('a', 'e'), ('b', 'c'), ('b', 'd'), ('b', 'e'), ('c', 'd'), ('c', 'e'), ('d', 'e')], 'a', 'b')['path'] == ['a', 'c', 'b']
    rng = random.Random(865)
    pool = 'abcdefgh'
    for _ in range(1200):
        nodes = rng.sample(pool, rng.randint(2, 8))
        allp = [(x, y) for i, x in enumerate(nodes) for y in nodes[i + 1:]]
        es = rng.sample(allp, rng.randint(1, min(10, len(allp))))
        es = [rng.choice((list, tuple))(e if rng.random() < .5 else e[::-1]) for e in es]
        named = sorted({n for e in es for n in e})
        if len(named) < 2:
            continue
        s, g = rng.sample(named, 2)
        assert f(es, s, g) == _oracle(es, s, g), (es, s, g)


def _late(m):
    f = m.lateral_route
    ET = 'edges must be a list or tuple'
    ES = 'edges must contain 1 to 10 entries'
    EE = 'each edge must be an (a, b) tuple'
    FE = 'each first end must be a printable ASCII string of 1 to 12 characters'
    SE = 'each second end must be a printable ASCII string of 1 to 12 characters'
    DF = 'the ends of an edge must differ'
    ED = 'edges must be distinct'
    NN = 'edges must name at most 8 nodes'
    ST = 'start must be a printable ASCII string of 1 to 12 characters'
    GL = 'goal must be a printable ASCII string of 1 to 12 characters'
    SG = 'start and goal must differ'
    NM = 'start and goal must be named in edges'
    ok = [('a', 'b'), ('b', 'c')]
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661',
             '\n', 'a\n', '\ta', 'a\x00', '\x7f', 'a\r', '\x1b[0m', 'a\x0b')
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, ET, f, bad, 'a', 'c')
    _raises(ValueError, ES, f, [], 'a', 'c')
    _raises(ValueError, ES, f, [('a', 'b')] * 11, 'a', 'c')
    for bad in ('ab', None, 5, ('a',), ('a', 'b', 'c'), (), {'a': 1}, L(['a', 'b']), T(('a', 'b'))):
        _raises(ValueError, EE, f, [bad], 'a', 'c')
        _raises(ValueError, EE, f, [('a', 'b'), bad], 'a', 'c')
    for bad in names:
        _raises(ValueError, FE, f, [(bad, 'b')], 'a', 'c')
        _raises(ValueError, FE, f, [('a', 'b'), (bad, 'c')], 'a', 'c')
        _raises(ValueError, SE, f, [('a', bad)], 'a', 'c')
        _raises(ValueError, SE, f, [('a', 'b'), ('b', bad)], 'a', 'c')
        _raises(ValueError, ST, f, ok, bad, 'c')
        _raises(ValueError, GL, f, ok, 'a', bad)
    f([(' ', 'A~ z')], ' ', 'A~ z')
    _raises(ValueError, DF, f, [('a', 'a')], 'a', 'c')
    _raises(ValueError, DF, f, [('a', 'b'), ('c', 'c')], 'a', 'c')
    _raises(ValueError, ED, f, [('a', 'b'), ('a', 'b')], 'a', 'b')
    _raises(ValueError, ED, f, [('a', 'b'), ('b', 'a')], 'a', 'b')
    _raises(ValueError, ED, f, [('a', 'b'), ['b', 'a']], 'a', 'b')
    _raises(ValueError, ED, f, [['a', 'b'], ('b', 'a')], 'a', 'b')
    nine = [(chr(97 + i), chr(98 + i)) for i in range(8)]
    _raises(ValueError, NN, f, nine, 'a', 'i')
    f(nine[:7], 'a', 'h')
    _raises(ValueError, NN, f, nine, 'a', 'zz')
    six = [(x, y) for i, x in enumerate('abcdef') for y in 'abcdef'[i + 1:]][:11]
    _raises(ValueError, ES, f, six, 'a', 'b')
    _raises(ValueError, SG, f, ok, 'a', 'a')
    _raises(ValueError, NM, f, ok, 'a', 'z')
    _raises(ValueError, NM, f, ok, 'z', 'a')
    _raises(ValueError, NM, f, ok, 'A', 'c')
    f(ok, 'a', 'c')
    # validation order
    _raises(TypeError, ET, f, None, None, None)
    _raises(ValueError, ES, f, [], None, None)
    _raises(ValueError, EE, f, [1], None, None)
    _raises(ValueError, FE, f, [(1, 1)], None, None)
    _raises(ValueError, SE, f, [('a', 1)], None, None)
    _raises(ValueError, DF, f, [('a', 'a'), ('a', 'a')], None, None)
    _raises(ValueError, ED, f, [('a', 'b'), ('a', 'b')], None, None)
    _raises(ValueError, NN, f, nine, None, None)
    _raises(ValueError, ST, f, ok, None, None)
    _raises(ValueError, GL, f, ok, 'a', None)
    _raises(ValueError, SG, f, ok, 'z', 'z')


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


LB = "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"
MUTANTS = [
    (LB, "isinstance(x, str) and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isalnum() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 0 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) < 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 13"),
    ("type(edges) not in (list, tuple)", "not isinstance(edges, (list, tuple))"),
    ("not 1 <= len(edges) <= 10", "not 0 <= len(edges) <= 10"),
    ("not 1 <= len(edges) <= 10", "not 1 <= len(edges) < 10"),
    ("not 1 <= len(edges) <= 10", "not 1 <= len(edges) <= 11"),
    ("type(e) not in (list, tuple) or len(e) != 2", "not isinstance(e, (list, tuple)) or len(e) != 2"),
    ("type(e) not in (list, tuple) or len(e) != 2", "type(e) not in (list, tuple) or len(e) > 2"),
    ("type(e) not in (list, tuple) or len(e) != 2", "type(e) not in (list, tuple) or len(e) < 2"),
    ("        if a == b:\n            raise", "        if False:\n            raise"),
    ("links.append(frozenset((a, b)))", "links.append((a, b))"),
    ("if len(set(links)) != len(links):", "if False:"),
    ("if len(nodes) > 8:", "if len(nodes) > 9:"),
    ("if len(nodes) > 8:", "if len(nodes) >= 8:"),
    ("if start == goal:", "if False:"),
    ("if start not in nodes or goal not in nodes:", "if start not in nodes and goal not in nodes:"),
    ("if start not in nodes or goal not in nodes:", "if start not in nodes:"),
    ("if start not in nodes or goal not in nodes:", "if goal not in nodes:"),
    ("direct = frozenset((start, goal)) in links", "direct = bool(links)"),
    ("direct = frozenset((start, goal)) in links", "direct = frozenset((start, goal)) not in links"),
    ("if link == frozenset((start, goal)):\n            continue", "if False:\n            continue"),
    ("near[a].add(b)", "pass"),
    ("near[b].add(a)", "pass"),
    ("dist = {goal: 0}", "dist = {start: 0}"),
    ("frontier = [goal]", "frontier = [start]"),
    ("dist[m] = dist[n] + 1", "dist[m] = dist[n] + 2"),
    ("if start not in dist:", "if False:"),
    ("path = [start]", "path = []"),
    ("min(m for m in near[path[-1]] if dist.get(m) == dist[path[-1]] - 1)", "max(m for m in near[path[-1]] if dist.get(m) == dist[path[-1]] - 1)"),
    ("'hops': dist[start], 'detour': dist[start] - 1", "'hops': dist[start] - 1, 'detour': dist[start] - 1"),
    ("'hops': dist[start], 'detour': dist[start] - 1", "'hops': dist[start], 'detour': dist[start]"),
    ("'hops': dist[start], 'detour': dist[start] - 1", "'hops': len(path), 'detour': dist[start] - 1"),
    ("return {'direct': direct, 'path': None, 'hops': None, 'detour': None}", "return {'direct': False, 'path': None, 'hops': None, 'detour': None}"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
