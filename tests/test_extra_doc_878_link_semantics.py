import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import link_semantics as mod

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
    assert mod.SCOPE == 'PARTIAL: links supplied two-feature bit masks by shared-bit count, no meanings are inferred'
    assert mod.NOT_CLAIMED == ('meaning inference', 'natural language understanding', 'semantic truth', 'feature extraction', 'production readiness')
    assert 'Semantic Networks - Links meanings' in mod.__doc__ and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(rows, shared):
    # Independent bit-position membership tests, no bitwise intersection/count.
    links = []
    for a,x,y in rows:
        for b,u,v in rows:
            count = sum(x//(2**k)%2==1 and u//(2**k)%2==1 for k in range(4))
            count += sum(y//(2**k)%2==1 and v//(2**k)%2==1 for k in range(4))
            if a<b and count>=shared:
                links.append((a,b,count))
    links.sort()
    names = sorted(n for n,_,_ in rows)
    adj = {n:sorted(b if a==n else a for a,b,c in links if n in (a,b)) for n in names}
    return {'links':links,'adjacency':adj,'isolated':[n for n in names if len(adj[n])==0]}


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
    f = m.link_semantics
    rows = [('z',3,0),('a',1,1),('b',3,1),('c',0,0)]
    assert f(rows) == {'links':[('a','b',2),('b','z',2)],'adjacency':{'a':['b'],'b':['a','z'],'c':[],'z':['b']},'isolated':['c']}
    assert f(rows,1) == _oracle(rows,1)
    assert f([('a',15,15),('b',15,15)],8)['links'] == [('a','b',8)]
    assert f([('a',15,15),('b',15,14)],8)['links'] == []
    assert f([('a',1,0),('b',0,1)],1)['links'] == []
    # Mixed raw list/tuple entries, in both orders, and tuple outer container.
    rows = [('a', 0, 15), ('b', 15, 0)]
    expected = _oracle(rows, 2)
    assert f([list(rows[0]), rows[1]]) == expected
    assert f([rows[0], list(rows[1])]) == expected
    assert f(tuple(map(list, rows))) == expected
    assert f([(' ', 0, 0), ('A~ z', 15, 15)]) == _oracle([(' ', 0, 0), ('A~ z', 15, 15)], 2)
    assert f([('x' * 12, 0, 15)]) == _oracle([('x' * 12, 0, 15)], 2)
    rng = random.Random(878)
    for _ in range(700):
        rows = [(chr(97+i), rng.randint(0, 15), rng.randint(0, 15)) for i in range(rng.randint(1,8))]
        rng.shuffle(rows)
        rows = [rng.choice((list, tuple))(r) for r in rows]
        p = rng.randint(1, 8)
        assert f(rows,p) == _oracle(rows,p), (rows,p)
        assert f(rows) == _oracle(rows,2)


def _late(m):
    f = m.link_semantics
    good = ('a', 0, 15)
    RT = 'rows must be a list or tuple'
    RS = 'rows must contain 1 to 8 entries'
    PA = 'shared must be a nonbool integer between 1 and 8'
    SH = 'each row must be a (label, x, y) triple'
    LA = 'label must be a printable ASCII string of 1 to 12 characters'
    X = 'x must be a nonbool integer between 0 and 15'
    Y = 'y must be a nonbool integer between 0 and 15'
    DU = 'labels must be distinct'
    for bad in (None, 'abc', 1, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, RT, f, bad)
    _raises(ValueError, RS, f, [])
    _raises(ValueError, RS, f, [(str(i),0,15) for i in range(9)])
    f([(str(i),0,15) for i in range(8)])
    for bad in (0, 9, True, False, 1.0, '1', None, I(1), LyingI(1), I(10**30), LyingI(10**30)):
        _raises(ValueError, PA, f, [good], bad)
    for p in (1, 8):
        f([good],p)
    for bad in (None, 1, 'abc', {}, (), ('a',), ('a',0), ('a',0,15,0), L(good), T(good)):
        for prefix in ([], [('b',0,15)]):
            _raises(ValueError, SH, f, prefix+[bad])
    for bad in ('', 'x'*13, None, 1, True, b'a', ['a'], S('a'), LyingS('a'), '\u00e9', 'a\u00e9', '\u4e2d', '\u0661', '\n', 'a\n', '\t', '\x00', '\x7f', '\r', '\x0b', '\x1b[0m'):
        for prefix in ([], [('b',0,15)]):
            _raises(ValueError, LA, f, prefix+[(bad,0,15)])
    for bad in (-1,16,True,False,1.0,'1',None,I(0),LyingI(0),I(10**30),LyingI(10**30)):
        for prefix in ([], [('b',0,15)]):
            _raises(ValueError, X, f, prefix+[('a',bad,15)])
            _raises(ValueError, Y, f, prefix+[('a',0,bad)])
    f([('a',15,0)])
    _raises(ValueError, DU, f, [good, good])
    # Competing invalid fields pin the validation order.
    _raises(TypeError, RT, f, None, None)
    _raises(ValueError, RS, f, [], None)
    _raises(ValueError, PA, f, [None], None)
    _raises(ValueError, SH, f, [None])
    _raises(ValueError, LA, f, [(None,None,None)])
    _raises(ValueError, X, f, [('a',None,None)])
    _raises(ValueError, Y, f, [('a',0,None)])
    _raises(ValueError, Y, f, [good,('a',0,None)])
    _raises(ValueError, LA, f, [('a',0,15),('a',0,15),(None,0,15)])


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
    ("type(rows) not in (list, tuple)", "not isinstance(rows, (list, tuple))"),
    ("not 1 <= len(rows) <= 8", "not 0 <= len(rows) <= 8"),
    ("not 1 <= len(rows) <= 8", "not 1 <= len(rows) < 8"),
    ("not 1 <= len(rows) <= 8", "not 1 <= len(rows) <= 9"),
    ("type(row) not in (list, tuple) or len(row) != 3", "not isinstance(row, (list, tuple)) or len(row) != 3"),
    ("type(row) not in (list, tuple) or len(row) != 3", "type(row) not in (list, tuple) or len(row) < 3"),
    ("len({r[0] for r in clean}) != len(clean)", "False"),
    ("shared=2", "shared=1"),
]
MUTANTS += [('(x & u).bit_count()', '(x | u).bit_count()'), ('(y & v).bit_count()', '(y | v).bit_count()'), (' + (y & v).bit_count()', ''), ('overlap >= shared', 'overlap > shared'), ('overlap >= shared', 'overlap < shared'), ('key=lambda r: r[0]', 'key=lambda r: r[0], reverse=True'), ('adjacency[b].append(a)', 'adjacency[b].append(b)'), ('neighbors.sort()', 'neighbors.sort(reverse=True)'), ('if not adjacency[n]', 'if adjacency[n]')]
for _v, _lo, _hi in (('shared',1,8),('x',0,15),('y',0,15)):
    MUTANTS += _ints(_v, _lo, _hi)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
