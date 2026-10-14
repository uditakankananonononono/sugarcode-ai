import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import transaction_escrow_fixture as mod

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
    assert mod.SCOPE == 'PARTIAL: inventories abstract supplied escrow tallies, no property transaction'
    assert mod.NOT_CLAIMED == ('property transaction', 'escrow validity', 'asset valuation', 'legal transfer', 'production readiness')
    assert 'Property Transactions' in mod.__doc__ and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(rows, fee):
    out=[]
    for n,x,y in rows:
        v=x
        for i in range(y+fee): v-=1
        out.append((n,v))
    out.sort()
    return {'balance':out,'shortfall':[(n,abs(v)) for n,v in out if -v>0],
            'sufficient':[n for n,v in out if not -v>0],'total':sum(v for n,v in out)}


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
    f = m.transaction_escrow_fixture
    rows=[('z',5,3),('a',4,3),('b',8,2)]
    assert f(rows)=={'balance':[('a',-1),('b',4),('z',0)],'shortfall':[('a',1)],'sufficient':['b','z'],'total':3}
    assert f(rows,0)==_oracle(rows,0)
    assert f(rows,10)==_oracle(rows,10)
    # Mixed raw list/tuple entries, in both orders, and tuple outer container.
    rows = [('a', 0, 10), ('b', 10, 0)]
    expected = _oracle(rows, 2)
    assert f([list(rows[0]), rows[1]]) == expected
    assert f([rows[0], list(rows[1])]) == expected
    assert f(tuple(map(list, rows))) == expected
    assert f([(' ', 0, 0), ('A~ z', 10, 10)]) == _oracle([(' ', 0, 0), ('A~ z', 10, 10)], 2)
    assert f([('x' * 12, 0, 10)]) == _oracle([('x' * 12, 0, 10)], 2)
    rng = random.Random(1256)
    for _ in range(700):
        rows = [(chr(97+i), rng.randint(0, 10), rng.randint(0, 10)) for i in range(rng.randint(1,8))]
        rng.shuffle(rows)
        rows = [rng.choice((list, tuple))(r) for r in rows]
        p = rng.randint(0, 10)
        assert f(rows,p) == _oracle(rows,p), (rows,p)
        assert f(rows) == _oracle(rows,2)


def _late(m):
    f = m.transaction_escrow_fixture
    good = ('a', 0, 10)
    RT = 'rows must be a list or tuple'
    RS = 'rows must contain 1 to 8 entries'
    PA = 'fee must be a nonbool integer between 0 and 10'
    SH = 'each row must be a (label, x, y) triple'
    LA = 'label must be a printable ASCII string of 1 to 12 characters'
    X = 'x must be a nonbool integer between 0 and 10'
    Y = 'y must be a nonbool integer between 0 and 10'
    DU = 'labels must be distinct'
    for bad in (None, 'abc', 1, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, RT, f, bad)
    _raises(ValueError, RS, f, [])
    _raises(ValueError, RS, f, [(str(i),0,10) for i in range(9)])
    f([(str(i),0,10) for i in range(8)])
    for bad in (-1, 11, True, False, 1.0, '1', None, I(0), LyingI(0), I(10**30), LyingI(10**30)):
        _raises(ValueError, PA, f, [good], bad)
    for p in (0, 10):
        f([good],p)
    for bad in (None, 1, 'abc', {}, (), ('a',), ('a',0), ('a',0,10,0), L(good), T(good)):
        for prefix in ([], [('b',0,10)]):
            _raises(ValueError, SH, f, prefix+[bad])
    for bad in ('', 'x'*13, None, 1, True, b'a', ['a'], S('a'), LyingS('a'), '\u00e9', 'a\u00e9', '\u4e2d', '\u0661', '\n', 'a\n', '\t', '\x00', '\x7f', '\r', '\x0b', '\x1b[0m'):
        for prefix in ([], [('b',0,10)]):
            _raises(ValueError, LA, f, prefix+[(bad,0,10)])
    for bad in (-1,11,True,False,1.0,'1',None,I(0),LyingI(0),I(10**30),LyingI(10**30)):
        for prefix in ([], [('b',0,10)]):
            _raises(ValueError, X, f, prefix+[('a',bad,10)])
            _raises(ValueError, Y, f, prefix+[('a',0,bad)])
    f([('a',10,0)])
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
    _raises(ValueError, LA, f, [('a',0,10),('a',0,10),(None,0,10)])


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
    ("fee=2", "fee=0"),
]
MUTANTS += [('x-y-fee', 'x-y+fee'), ('v<0', 'v<=0'), ('v>=0', 'v>0'), ('sum(v for n,v in balance)', 'max(v for n,v in balance)'), ('key=lambda r:r[0]', 'key=lambda r:r[0], reverse=True')]
for _v, _lo, _hi in (('fee',0,10),('x',0,10),('y',0,10)):
    MUTANTS += _ints(_v, _lo, _hi)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
