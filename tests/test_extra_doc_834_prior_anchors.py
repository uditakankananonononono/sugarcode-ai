import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import prior_anchors as mod

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
    assert mod.SCOPE == 'PARTIAL: matches supplied concept links to a supplied known list, no knowledge is activated'
    assert len(mod.NOT_CLAIMED) == 5 and 'transfer of learning' in mod.NOT_CLAIMED and 'learner memory' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Prior Knowledge Activation - Connects to existing' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(kn, cs):
    """Independent: build an inverted view (known -> position) and walk the links with a plain loop."""
    pos = {}
    for i, k in enumerate(kn):
        pos[k] = i
    anchors, orph, ign = [], [], 0
    for n, ls in cs:
        found = []
        for l in ls:
            if l in pos:
                found.append(l)
            else:
                ign += 1
        found.sort()
        anchors.append((n, found))
        if not found:
            orph.append(n)
    done = len(cs) - len(orph)
    return {'anchors': anchors, 'orphans': orph, 'ignored': ign, 'linked_percent': int(done * 100 / len(cs)) if (done * 100) % len(cs) == 0 else (done * 100 - (done * 100) % len(cs)) // len(cs)}


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
    f = m.prior_anchors
    assert f(['a'], [('x', ['a'])]) == {'anchors': [('x', ['a'])], 'orphans': [], 'ignored': 0, 'linked_percent': 100}
    assert f(['a'], [('x', [])]) == {'anchors': [('x', [])], 'orphans': ['x'], 'ignored': 0, 'linked_percent': 0}
    assert f(['a'], [('x', ['b'])]) == {'anchors': [('x', [])], 'orphans': ['x'], 'ignored': 1, 'linked_percent': 0}
    r = f(['b', 'a', 'c'], [('x', ['c', 'a', 'z']), ('y', ['q']), ('w', ())])
    assert r == {'anchors': [('x', ['a', 'c']), ('y', []), ('w', [])], 'orphans': ['y', 'w'], 'ignored': 2, 'linked_percent': 33}
    r = f(('a', 'b'), (('x', ('a',)), ('y', ['b']), ('z', [])))
    assert r['linked_percent'] == 66 and r['orphans'] == ['z']
    assert f(['a', 'b'], [('x', ['a']), ('y', []), ('z', []), ('w', ['b'])])['linked_percent'] == 50
    assert f(['a'], [('q', ['a']), ('p', ['a'])])['anchors'] == [('q', ['a']), ('p', ['a'])]
    assert f(['a'], [('x', ['A'])])['orphans'] == ['x']
    assert f(['a'], [('x' * 12, ['a'])])['anchors'][0][0] == 'x' * 12
    assert f(['k' * 12], [('x', ['k' * 12])])['linked_percent'] == 100
    assert f(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'], [('x', ['h', 'g', 'f', 'e'])])['anchors'] == [('x', ['e', 'f', 'g', 'h'])]
    assert len(f(['a'], [(chr(97 + i), ['a']) for i in range(6)])['anchors']) == 6
    rng = random.Random(834)
    pool = 'abcdefghijkl'
    for _ in range(600):
        kn = rng.sample(pool, rng.randint(1, 8))
        cs = []
        for i in range(rng.randint(1, 6)):
            ls = rng.sample(pool, rng.randint(0, 4))
            cs.append((chr(109 + i), rng.choice((list, tuple))(ls)))
        assert f(kn, cs) == _oracle(kn, cs), (kn, cs)


def _late(m):
    f = m.prior_anchors
    KT = 'known must be a list or tuple'
    KS = 'known must contain 1 to 8 entries'
    KE = 'each known entry must be an ASCII string of 1 to 12 characters'
    KD = 'known entries must be distinct'
    CT = 'concepts must be a list or tuple'
    CS = 'concepts must contain 1 to 6 entries'
    CE = 'each concept must be a (name, links) tuple'
    NM = 'each name must be an ASCII string of 1 to 12 characters'
    LT = 'links must be a list or tuple'
    LS = 'links must contain 0 to 4 entries'
    LE = 'each link must be an ASCII string of 1 to 12 characters'
    LD = 'links must be distinct'
    ND = 'names must be distinct'
    ok = [('x', ['a'])]
    for bad in ('ab', None, 5, {}, L(['a']), T(['a']), L(), T()):
        _raises(TypeError, KT, f, bad, ok)
    _raises(ValueError, KS, f, [], ok)
    _raises(ValueError, KS, f, list('abcdefghi'), ok)
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661')
    for bad in names:
        _raises(ValueError, KE, f, [bad], ok)
        _raises(ValueError, KE, f, ['a', bad], ok)
    f(['A~ z'], ok)
    _raises(ValueError, KD, f, ['a', 'a'], ok)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, CT, f, ['a'], bad)
    _raises(ValueError, CS, f, ['a'], [])
    _raises(ValueError, CS, f, ['a'], [(chr(97 + i), []) for i in range(7)])
    for bad in ('ab', None, 5, ('x',), ('x', [], 1), (), {'x': 1}, L(['x', []]), T(('x', ()))):
        _raises(ValueError, CE, f, ['a'], [bad])
        _raises(ValueError, CE, f, ['a'], [('y', []), bad])
    for bad in names:
        _raises(ValueError, NM, f, ['a'], [(bad, [])])
        _raises(ValueError, NM, f, ['a'], [('y', []), (bad, [])])
    f(['a'], [('A~ z', [])])
    for bad in ('ab', None, 5, {}, {'a'}, L(['a']), T(['a']), L(), T()):
        _raises(ValueError, LT, f, ['a'], [('x', bad)])
        _raises(ValueError, LT, f, ['a'], [('y', []), ('x', bad)])
    _raises(ValueError, LS, f, ['a'], [('x', ['a', 'b', 'c', 'd', 'e'])])
    f(['a'], [('x', ['a', 'b', 'c', 'd'])])
    f(['a'], [('x', [])])
    for bad in names:
        _raises(ValueError, LE, f, ['a'], [('x', [bad])])
        _raises(ValueError, LE, f, ['a'], [('y', []), ('x', ['a', bad])])
    f(['a'], [('x', ['A~ z'])])
    _raises(ValueError, LD, f, ['a'], [('x', ['a', 'a'])])
    _raises(ValueError, ND, f, ['a'], [('x', []), ('x', [])])
    # validation order
    _raises(TypeError, KT, f, None, None)
    _raises(ValueError, KS, f, [], None)
    _raises(ValueError, KE, f, [1, 1], None)
    _raises(ValueError, KD, f, ['a', 'a'], None)
    _raises(TypeError, CT, f, ['a'], None)
    _raises(ValueError, CS, f, ['a'], [])
    _raises(ValueError, CE, f, ['a'], [1])
    _raises(ValueError, NM, f, ['a'], [(1, 5)])
    _raises(ValueError, LT, f, ['a'], [('x', 5)])
    _raises(ValueError, LS, f, ['a'], [('x', [1, 2, 3, 4, 5])])
    _raises(ValueError, LE, f, ['a'], [('x', [1, 1])])
    _raises(ValueError, LD, f, ['a'], [('x', ['a', 'a']), ('x', [])])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("type(x) is str and x.isascii() and 1 <= len(x) <= 12", "isinstance(x, str) and x.isascii() and 1 <= len(x) <= 12"),
    ("type(x) is str and x.isascii() and 1 <= len(x) <= 12", "type(x) is str and 1 <= len(x) <= 12"),
    ("type(x) is str and x.isascii() and 1 <= len(x) <= 12", "type(x) is str and x.isalnum() and 1 <= len(x) <= 12"),
    ("type(x) is str and x.isascii() and 1 <= len(x) <= 12", "type(x) is str and x.isascii() and 0 <= len(x) <= 12"),
    ("type(x) is str and x.isascii() and 1 <= len(x) <= 12", "type(x) is str and x.isascii() and 1 <= len(x) < 12"),
    ("type(x) is str and x.isascii() and 1 <= len(x) <= 12", "type(x) is str and x.isascii() and 1 <= len(x) <= 13"),
    ("type(known) not in (list, tuple)", "not isinstance(known, (list, tuple))"),
    ("not 1 <= len(known) <= 8", "not 0 <= len(known) <= 8"),
    ("not 1 <= len(known) <= 8", "not 1 <= len(known) < 8"),
    ("not 1 <= len(known) <= 8", "not 1 <= len(known) <= 9"),
    ("if len(set(known)) != len(known):", "if False:"),
    ("type(concepts) not in (list, tuple)", "not isinstance(concepts, (list, tuple))"),
    ("not 1 <= len(concepts) <= 6", "not 0 <= len(concepts) <= 6"),
    ("not 1 <= len(concepts) <= 6", "not 1 <= len(concepts) < 6"),
    ("not 1 <= len(concepts) <= 6", "not 1 <= len(concepts) <= 7"),
    ("type(c) not in (list, tuple) or len(c) != 2", "not isinstance(c, (list, tuple)) or len(c) != 2"),
    ("type(c) not in (list, tuple) or len(c) != 2", "type(c) not in (list, tuple) or len(c) > 2"),
    ("type(c) not in (list, tuple) or len(c) != 2", "type(c) not in (list, tuple) or len(c) < 2"),
    ("type(links) not in (list, tuple)", "not isinstance(links, (list, tuple))"),
    ("if len(links) > 4:", "if len(links) > 5:"),
    ("if len(links) > 4:", "if len(links) >= 4:"),
    ("if len(set(links)) != len(links):", "if False:"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("hit = sorted(k for k in links if k in known)", "hit = [k for k in links if k in known]"),
    ("hit = sorted(k for k in links if k in known)", "hit = sorted(k for k in links if k in known)[:1]"),
    ("hit = sorted(k for k in links if k in known)", "hit = sorted(k for k in links)"),
    ("hit = sorted(k for k in links if k in known)", "hit = sorted(k for k in links if k.lower() in known)"),
    ("ignored += len(links) - len(hit)", "ignored += len(links)"),
    ("ignored += len(links) - len(hit)", "ignored = len(links) - len(hit)"),
    ("ignored += len(links) - len(hit)", "ignored += 0"),
    ("orphans = [n for n, hit in anchors if not hit]", "orphans = sorted(n for n, hit in anchors if not hit)"),
    ("orphans = [n for n, hit in anchors if not hit]", "orphans = [n for n, hit in anchors if len(hit) < 2]"),
    ("(len(anchors) - len(orphans)) * 100 // len(anchors)", "(len(anchors) - len(orphans)) * 100 // len(anchors) + 1"),
    ("(len(anchors) - len(orphans)) * 100 // len(anchors)", "round((len(anchors) - len(orphans)) * 100 / len(anchors))"),
    ("(len(anchors) - len(orphans)) * 100 // len(anchors)", "len(orphans) * 100 // len(anchors)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
