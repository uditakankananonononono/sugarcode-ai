import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import organize_shelves as mod

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
    assert mod.SCOPE == 'PARTIAL: first-fit-decreasing packing of supplied information sizes, no knowledge is understood'
    assert mod.NOT_CLAIMED == ('knowledge understanding', 'optimal packing', 'semantic organization', 'size estimation', 'production readiness')
    assert 'Knowledge Organization - Structures information' in mod.__doc__ and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(rows, capacity):
    # Independent rank-count order and recomputed shelf sums, no running loads.
    order = []
    for i in range(len(rows)):
        for r in rows:
            rank = sum(a+b>r[1]+r[2] or (a+b==r[1]+r[2] and n<r[0]) for n,a,b in rows)
            if rank==i:
                order.append(r)
    shelves = []
    sizes = {n:x+y for n,x,y in rows}
    rejected = []
    for n,x,y in order:
        if x+y>capacity:
            rejected.append(n)
        else:
            fit = next((b for b in shelves if sum(sizes[k] for k in b)+x+y<=capacity),None)
            if fit is None:
                shelves.append([n])
            else:
                fit.append(n)
    return {'shelves':shelves,'loads':[sum(sizes[n] for n in b) for b in shelves],'rejected':rejected}


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
    f = m.organize_shelves
    rows = [('z',40,0),('a',60,0),('b',50,0),('c',0,0),('d',100,1)]
    assert f(rows) == {'shelves':[['a','z','c'],['b']],'loads':[100,50],'rejected':['d']}
    assert f(rows,200) == _oracle(rows,200)
    assert f([('a',100,100)],1) == {'shelves':[],'loads':[],'rejected':['a']}
    assert f([('a',0,0),('b',0,0)]) == {'shelves':[['a','b']],'loads':[0],'rejected':[]}
    assert f([('a',6,0),('b',4,0),('c',5,0)],10) == _oracle([('a',6,0),('b',4,0),('c',5,0)],10)
    # Mixed raw list/tuple entries, in both orders, and tuple outer container.
    rows = [('a', 0, 100), ('b', 100, 0)]
    expected = _oracle(rows, 100)
    assert f([list(rows[0]), rows[1]]) == expected
    assert f([rows[0], list(rows[1])]) == expected
    assert f(tuple(map(list, rows))) == expected
    assert f([(' ', 0, 0), ('A~ z', 100, 100)]) == _oracle([(' ', 0, 0), ('A~ z', 100, 100)], 100)
    assert f([('x' * 12, 0, 100)]) == _oracle([('x' * 12, 0, 100)], 100)
    rng = random.Random(875)
    for _ in range(700):
        rows = [(chr(97+i), rng.randint(0, 100), rng.randint(0, 100)) for i in range(rng.randint(1,8))]
        rng.shuffle(rows)
        rows = [rng.choice((list, tuple))(r) for r in rows]
        p = rng.randint(1, 200)
        assert f(rows,p) == _oracle(rows,p), (rows,p)
        assert f(rows) == _oracle(rows,100)


def _late(m):
    f = m.organize_shelves
    good = ('a', 0, 100)
    RT = 'rows must be a list or tuple'
    RS = 'rows must contain 1 to 8 entries'
    PA = 'capacity must be a nonbool integer between 1 and 200'
    SH = 'each row must be a (label, x, y) triple'
    LA = 'label must be a printable ASCII string of 1 to 12 characters'
    X = 'x must be a nonbool integer between 0 and 100'
    Y = 'y must be a nonbool integer between 0 and 100'
    DU = 'labels must be distinct'
    for bad in (None, 'abc', 1, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, RT, f, bad)
    _raises(ValueError, RS, f, [])
    _raises(ValueError, RS, f, [(str(i),0,100) for i in range(9)])
    f([(str(i),0,100) for i in range(8)])
    for bad in (0, 201, True, False, 1.0, '1', None, I(1), LyingI(1), I(10**30), LyingI(10**30)):
        _raises(ValueError, PA, f, [good], bad)
    for p in (1, 200):
        f([good],p)
    for bad in (None, 1, 'abc', {}, (), ('a',), ('a',0), ('a',0,100,0), L(good), T(good)):
        for prefix in ([], [('b',0,100)]):
            _raises(ValueError, SH, f, prefix+[bad])
    for bad in ('', 'x'*13, None, 1, True, b'a', ['a'], S('a'), LyingS('a'), '\u00e9', 'a\u00e9', '\u4e2d', '\u0661', '\n', 'a\n', '\t', '\x00', '\x7f', '\r', '\x0b', '\x1b[0m'):
        for prefix in ([], [('b',0,100)]):
            _raises(ValueError, LA, f, prefix+[(bad,0,100)])
    for bad in (-1,101,True,False,1.0,'1',None,I(0),LyingI(0),I(10**30),LyingI(10**30)):
        for prefix in ([], [('b',0,100)]):
            _raises(ValueError, X, f, prefix+[('a',bad,100)])
            _raises(ValueError, Y, f, prefix+[('a',0,bad)])
    f([('a',100,0)])
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
    _raises(ValueError, LA, f, [('a',0,100),('a',0,100),(None,0,100)])


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
    ("capacity=100", "capacity=1"),
]
MUTANTS += [('-(r[1] + r[2])', 'r[1] + r[2]'), ('size = x + y', 'size = x'), ('size > capacity', 'size >= capacity'), ('load + size <= capacity', 'load + size < capacity'), ('loads[i] += size', 'loads[i] += 0'), ('for i, load in enumerate(loads):', 'for i, load in reversed(list(enumerate(loads))):'), ('rejected.append(label)', 'rejected.insert(0, label)'), ('shelves[i].append(label)', 'shelves[i].insert(0, label)')]
for _v, _lo, _hi in (('capacity',1,200),('x',0,100),('y',0,100)):
    MUTANTS += _ints(_v, _lo, _hi)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
