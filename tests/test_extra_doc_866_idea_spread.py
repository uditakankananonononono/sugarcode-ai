import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import idea_spread as mod

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
    assert mod.SCOPE == 'PARTIAL: counts supplied ideas and their categories, no thinking is assessed'
    assert len(mod.NOT_CLAIMED) == 5 and 'quality of ideas' in mod.NOT_CLAIMED and 'originality' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Divergent Thinking - Generates many ideas' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(es, mc):
    """Independent: tally with a list of [category, count] cells, then order by a scan for the best cell each time."""
    cells = []
    for _, c in es:
        for cell in cells:
            if cell[0] == c:
                cell[1] += 1
                break
        else:
            cells.append([c, 1])
    left = [tuple(x) for x in cells]
    out = []
    while left:
        pick = left[0]
        for x in left[1:]:
            if x[1] > pick[1] or (x[1] == pick[1] and x[0] < pick[0]):
                pick = x
        out.append(pick)
        left.remove(pick)
    n = len(es)
    pct = 0
    while (pct + 1) * n <= out[0][1] * 100:
        pct += 1
    return {'fluency': n, 'flexibility': len(out), 'by_category': out, 'top_percent': pct,
            'balanced': out[0][1] <= n - out[0][1], 'diverse': len(out) >= mc}


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
    f = m.idea_spread
    assert f([('i', 'c')]) == {'fluency': 1, 'flexibility': 1, 'by_category': [('c', 1)], 'top_percent': 100, 'balanced': False, 'diverse': False}
    assert f([('i', 'c'), ('j', 'd')]) == {'fluency': 2, 'flexibility': 2, 'by_category': [('c', 1), ('d', 1)], 'top_percent': 50, 'balanced': True, 'diverse': False}
    # balanced is exact at half: 2 of 4 balanced, 3 of 5 not, 2 of 5 yes
    assert f([('a', 'x'), ('b', 'x'), ('c', 'y'), ('d', 'z')])['balanced'] is True
    assert f([('a', 'x'), ('b', 'x'), ('c', 'x'), ('d', 'y'), ('e', 'z')])['balanced'] is False
    assert f([('a', 'x'), ('b', 'x'), ('c', 'y'), ('d', 'z'), ('e', 'w')])['balanced'] is True
    assert f([('a', 'x'), ('b', 'x'), ('c', 'x'), ('d', 'y')])['balanced'] is False
    # default min_categories 3: two categories not diverse, three are; 2 and 4 move the edge
    two = [('a', 'x'), ('b', 'y'), ('c', 'x')]
    three = [('a', 'x'), ('b', 'y'), ('c', 'z')]
    assert f(two)['diverse'] is False and f(three)['diverse'] is True and f(three) == f(three, 3)
    assert f(two, 2)['diverse'] is True and f(three, 4)['diverse'] is False and f(three, 1)['diverse'] is True
    assert f([(chr(97 + i), chr(97 + i)) for i in range(6)], 6)['diverse'] is True
    assert f([(chr(97 + i), chr(97 + i)) for i in range(5)], 6)['diverse'] is False
    # ordering: biggest count first, ties by category, regardless of input order
    es = [('1', 'm'), ('2', 'b'), ('3', 'b'), ('4', 'z'), ('5', 'z'), ('6', 'a')]
    assert f(es)['by_category'] == [('b', 2), ('z', 2), ('a', 1), ('m', 1)]
    assert f(es[::-1])['by_category'] == [('b', 2), ('z', 2), ('a', 1), ('m', 1)]
    assert f(es)['top_percent'] == 33
    assert f([('a', 'x')] * 0 + [(str(i), 'x') for i in range(7)] + [('q', 'y'), ('r', 'z'), ('s', 'w')])['top_percent'] == 70
    assert f([('a', 'x'), ('b', 'x'), ('c', 'y')])['top_percent'] == 66
    # mixed list and tuple entries, in both orders
    assert f([('a', 'x'), ['b', 'y'], ('c', 'z')]) == f(three)
    assert f([['a', 'x'], ('b', 'y'), ['c', 'z']]) == f(three)
    assert f((['a', 'x'], ('b', 'y')))['flexibility'] == 2
    assert f([('x' * 12, 'A~ z')])['by_category'] == [('A~ z', 1)]
    assert f([(chr(97 + i), 'c') for i in range(10)])['fluency'] == 10
    rng = random.Random(866)
    for _ in range(1200):
        n = rng.randint(1, 10)
        es2 = [(chr(97 + i), rng.choice('pqrstu')) for i in range(n)]
        es2 = [rng.choice((list, tuple))(e) for e in es2]
        mc = rng.randint(1, 6)
        assert f(es2, mc) == _oracle(es2, mc), (es2, mc)
        assert f(es2) == _oracle(es2, 3)


def _late(m):
    f = m.idea_spread
    MC = 'min_categories must be a nonbool integer between 1 and 6'
    IT = 'ideas must be a list or tuple'
    IS = 'ideas must contain 1 to 10 entries'
    EE = 'each entry must be an (idea, category) tuple'
    ID = 'each idea must be a printable ASCII string of 1 to 12 characters'
    CA = 'each category must be a printable ASCII string of 1 to 12 characters'
    DI = 'ideas must be distinct'
    ok = [('a', 'x')]
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661',
             '\n', 'a\n', '\ta', 'a\x00', '\x7f', 'a\r', '\x1b[0m', 'a\x0b')
    for bad in (0, 7, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MC, f, ok, bad)
    f(ok, 1)
    f(ok, 6)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, IT, f, bad)
    _raises(ValueError, IS, f, [])
    _raises(ValueError, IS, f, [(str(i), 'x') for i in range(11)])
    f([(str(i), 'x') for i in range(10)])
    for bad in ('ab', None, 5, ('a',), ('a', 'x', 'y'), (), {'a': 1}, L(['a', 'x']), T(('a', 'x'))):
        _raises(ValueError, EE, f, [bad])
        _raises(ValueError, EE, f, [('b', 'x'), bad])
    for bad in names:
        _raises(ValueError, ID, f, [(bad, 'x')])
        _raises(ValueError, ID, f, [('b', 'x'), (bad, 'x')])
        _raises(ValueError, CA, f, [('a', bad)])
        _raises(ValueError, CA, f, [('b', 'x'), ('a', bad)])
    f([(' ', 'A~ z')])
    _raises(ValueError, DI, f, [('a', 'x'), ('a', 'y')])
    _raises(ValueError, DI, f, [('a', 'x'), ['a', 'x']])
    _raises(ValueError, MC, f, None, 0)
    _raises(TypeError, IT, f, None, 3)
    _raises(ValueError, IS, f, [], 3)
    _raises(ValueError, EE, f, [1], 3)
    _raises(ValueError, ID, f, [(1, 1)], 3)
    _raises(ValueError, CA, f, [('a', 1), ('a', 1)], 3)
    _raises(ValueError, DI, f, [('a', 'x'), ('a', 'y')], 3)


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
    ("min_categories=3", "min_categories=2"),
    ("min_categories=3", "min_categories=4"),
    (LB, "isinstance(x, str) and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isalnum() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 0 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) < 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 13"),
    ("type(ideas) not in (list, tuple)", "not isinstance(ideas, (list, tuple))"),
    ("not 1 <= len(ideas) <= 10", "not 0 <= len(ideas) <= 10"),
    ("not 1 <= len(ideas) <= 10", "not 1 <= len(ideas) < 10"),
    ("not 1 <= len(ideas) <= 10", "not 1 <= len(ideas) <= 11"),
    ("type(e) not in (list, tuple) or len(e) != 2", "not isinstance(e, (list, tuple)) or len(e) != 2"),
    ("type(e) not in (list, tuple) or len(e) != 2", "type(e) not in (list, tuple) or len(e) > 2"),
    ("type(e) not in (list, tuple) or len(e) != 2", "type(e) not in (list, tuple) or len(e) < 2"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("len({r[0] for r in rows}) != len(rows)", "len({r[1] for r in rows}) != len(rows)"),
    ("counts[category] = counts.get(category, 0) + 1", "counts[category] = 1"),
    ("key=lambda kv: (-kv[1], kv[0])", "key=lambda kv: (kv[1], kv[0])"),
    ("key=lambda kv: (-kv[1], kv[0])", "key=lambda kv: (-kv[1], kv[0]), reverse=True"),
    ("key=lambda kv: (-kv[1], kv[0])", "key=lambda kv: kv[0]"),
    ("key=lambda kv: (-kv[1], kv[0])", "key=lambda kv: -kv[1]"),
    ("top = ordered[0][1]", "top = ordered[-1][1]"),
    ("'fluency': len(rows)", "'fluency': len(counts)"),
    ("'flexibility': len(counts)", "'flexibility': len(rows)"),
    ("top * 100 // len(rows)", "(top * 100 + len(rows) - 1) // len(rows)"),
    ("top * 100 // len(rows)", "round(top * 100 / len(rows))"),
    ("top * 100 // len(rows)", "top * 100 // len(counts)"),
    ("'balanced': top * 2 <= len(rows)", "'balanced': top * 2 < len(rows)"),
    ("'balanced': top * 2 <= len(rows)", "'balanced': top * 3 <= len(rows)"),
    ("'diverse': len(counts) >= min_categories", "'diverse': len(counts) > min_categories"),
    ("'diverse': len(counts) >= min_categories", "'diverse': len(rows) >= min_categories"),
]
MUTANTS += _ints('min_categories', 1, 6)


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
