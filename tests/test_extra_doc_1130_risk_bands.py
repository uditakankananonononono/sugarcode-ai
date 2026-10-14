import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import risk_bands as mod

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
    assert mod.SCOPE == 'PARTIAL: places supplied scores into caller-scaled numeric bands, no patient risk is estimated'
    assert mod.NOT_CLAIMED == ('patient risk', 'clinical strata', 'predictive validity', 'score provenance', 'production readiness')
    assert 'Patient Risk Stratification' in mod.__doc__ and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(rows, width):
    # Independent repeated subtraction for band assignment.
    bands=[]
    for n,x,y in rows:
        v=x+y; k=0
        while v>=width: v-=width; k+=1
        bands.append((n,k))
    bands.sort(); levels=sorted(set(k for n,k in bands))
    return {'bands':bands,'groups':{k:[n for n,b in bands if b==k] for k in levels},'top':levels[-1]}


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
    f = m.risk_bands
    rows=[('z',10,10),('a',0,19),('b',100,100)]
    assert f(rows) == {'bands':[('a',0),('b',10),('z',1)],'groups':{0:['a'],1:['z'],10:['b']},'top':10}
    assert f(rows,1) == _oracle(rows,1)
    assert f(rows,100) == _oracle(rows,100)
    assert f([('a',20,0)])['bands'] == [('a',1)]
    # Mixed raw list/tuple entries, in both orders, and tuple outer container.
    rows = [('a', 0, 100), ('b', 100, 0)]
    expected = _oracle(rows, 20)
    assert f([list(rows[0]), rows[1]]) == expected
    assert f([rows[0], list(rows[1])]) == expected
    assert f(tuple(map(list, rows))) == expected
    assert f([(' ', 0, 0), ('A~ z', 100, 100)]) == _oracle([(' ', 0, 0), ('A~ z', 100, 100)], 20)
    assert f([('x' * 12, 0, 100)]) == _oracle([('x' * 12, 0, 100)], 20)
    assert list(f([('a',100,100),('b',0,0),('c',20,0)])['groups']) == [0,1,10]
    rng = random.Random(1130)
    for _ in range(700):
        rows = [(chr(97+i), rng.randint(0, 100), rng.randint(0, 100)) for i in range(rng.randint(1,8))]
        rng.shuffle(rows)
        rows = [rng.choice((list, tuple))(r) for r in rows]
        p = rng.randint(1, 100)
        assert f(rows,p) == _oracle(rows,p), (rows,p)
        assert f(rows) == _oracle(rows,20)


def _late(m):
    f = m.risk_bands
    good = ('a', 0, 100)
    RT = 'rows must be a list or tuple'
    RS = 'rows must contain 1 to 8 entries'
    PA = 'width must be a nonbool integer between 1 and 100'
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
    for bad in (0, 101, True, False, 1.0, '1', None, I(1), LyingI(1), I(10**30), LyingI(10**30)):
        _raises(ValueError, PA, f, [good], bad)
    for p in (1, 100):
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
    ("width=20", "width=1"),
]
MUTANTS += [('(first + second) // width', '(first + second + width - 1) // width'), ('first + second', 'first - second'), ('key=lambda r: r[0]', 'key=lambda r: r[0], reverse=True'), ('max(band for n, band', 'min(band for n, band'), ('for k in sorted(groups)', 'for k in sorted(groups, reverse=True)')]
for _v, _lo, _hi in (('width',1,100),('x',0,100),('y',0,100)):
    MUTANTS += _ints(_v, _lo, _hi)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
