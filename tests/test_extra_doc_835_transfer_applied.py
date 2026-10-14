import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import transfer_applied as mod

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
    assert mod.SCOPE == 'PARTIAL: tallies supplied trial outcomes in contexts outside a supplied taught list, no learner transfers'
    assert len(mod.NOT_CLAIMED) == 5 and 'task similarity' in mod.NOT_CLAIMED and 'learner ability' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Transfer - Applies to new contexts' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(td, tr):
    """Independent: partition trials with a dict of context -> (a, s), then fractions via exact cross-multiplication."""
    book = {c: (a, s) for c, a, s in tr}
    new = [v for c, v in book.items() if td.count(c) == 0]
    old = [v for c, v in book.items() if td.count(c) > 0]
    na = sum(v[0] for v in new)
    ns = sum(v[1] for v in new)
    pct = 0
    while na and (pct + 1) * na <= ns * 100:
        pct += 1
    return {'new_attempts': na, 'new_successes': ns, 'familiar_attempts': sum(v[0] for v in old),
            'new_percent': pct, 'applied': ns > 0 and 2 * ns >= na}


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
    f = m.transfer_applied
    assert f(['a'], [('b', 4, 3)]) == {'new_attempts': 4, 'new_successes': 3, 'familiar_attempts': 0, 'new_percent': 75, 'applied': True}
    assert f(['a'], [('a', 4, 3)]) == {'new_attempts': 0, 'new_successes': 0, 'familiar_attempts': 4, 'new_percent': 0, 'applied': False}
    assert f(['a'], [('b', 4, 0)]) == {'new_attempts': 4, 'new_successes': 0, 'familiar_attempts': 0, 'new_percent': 0, 'applied': False}
    assert f(['a'], [('b', 3, 1)])['new_percent'] == 33 and f(['a'], [('b', 3, 1)])['applied'] is False
    assert f(['a'], [('b', 2, 1)])['applied'] is True and f(['a'], [('b', 3, 2)])['applied'] is True
    assert f(['a'], [('b', 5, 2)])['applied'] is False and f(['a'], [('b', 5, 3)])['applied'] is True
    assert f(['a'], [('b', 1, 1)])['new_percent'] == 100 and f(['a'], [('b', 10, 10)])['applied'] is True
    r = f(['a', 'b'], [('a', 5, 5), ('c', 2, 1), ('b', 3, 0), ('d', 4, 2), ('e', 1, 0)])
    assert r == {'new_attempts': 7, 'new_successes': 3, 'familiar_attempts': 8, 'new_percent': 42, 'applied': False}
    r = f(('a', 'b'), (['a', 5, 5], ('c', 2, 2), ['d', 4, 1]))
    assert r['new_attempts'] == 6 and r['new_successes'] == 3 and r['applied'] is True and r['new_percent'] == 50
    assert f(['a'], [('A', 2, 2)])['new_attempts'] == 2
    assert f(['k' * 12], [('k' * 12, 2, 1), ('j', 1, 1)])['familiar_attempts'] == 2
    assert f(['a'], [(chr(98 + i), 1, 1) for i in range(8)])['new_attempts'] == 8
    assert f(list('abcdef'), [('a', 1, 1), ('g', 1, 1)])['new_attempts'] == 1
    rng = random.Random(835)
    pool = 'abcdefghij'
    for _ in range(600):
        td = rng.sample(pool, rng.randint(1, 6))
        cs = rng.sample(pool, rng.randint(1, 8))
        tr = []
        for c in cs:
            a = rng.randint(1, 10)
            tr.append((c, a, rng.randint(0, a)))
        assert f(td, tr) == _oracle(td, tr), (td, tr)


def _late(m):
    f = m.transfer_applied
    TT = 'taught must be a list or tuple'
    TS = 'taught must contain 1 to 6 entries'
    TE = 'each taught entry must be an ASCII string of 1 to 12 characters'
    TD = 'taught entries must be distinct'
    RT = 'trials must be a list or tuple'
    RS = 'trials must contain 1 to 8 entries'
    RE = 'each trial must be a (context, attempts, successes) tuple'
    CX = 'each context must be an ASCII string of 1 to 12 characters'
    AT = 'attempts must be a nonbool integer between 1 and 10'
    SU = 'successes must be a nonbool integer between 0 and attempts'
    CD = 'contexts must be distinct'
    ok = [('x', 1, 1)]
    for bad in ('ab', None, 5, {}, L(['a']), T(['a']), L(), T()):
        _raises(TypeError, TT, f, bad, ok)
    _raises(ValueError, TS, f, [], ok)
    _raises(ValueError, TS, f, list('abcdefg'), ok)
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661')
    for bad in names:
        _raises(ValueError, TE, f, [bad], ok)
        _raises(ValueError, TE, f, ['a', bad], ok)
    f(['A~ z'], ok)
    _raises(ValueError, TD, f, ['a', 'a'], ok)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, RT, f, ['a'], bad)
    _raises(ValueError, RS, f, ['a'], [])
    _raises(ValueError, RS, f, ['a'], [(chr(97 + i), 1, 1) for i in range(9)])
    for bad in ('ab', None, 5, ('x', 1), ('x', 1, 1, 1), (), {'x': 1}, L(['x', 1, 1]), T(('x', 1, 1))):
        _raises(ValueError, RE, f, ['a'], [bad])
        _raises(ValueError, RE, f, ['a'], [('y', 1, 1), bad])
    for bad in names:
        _raises(ValueError, CX, f, ['a'], [(bad, 1, 1)])
        _raises(ValueError, CX, f, ['a'], [('y', 1, 1), (bad, 1, 1)])
    f(['a'], [('A~ z', 1, 1)])
    for bad in (0, 11, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, AT, f, ['a'], [('x', bad, 0)])
        _raises(ValueError, AT, f, ['a'], [('y', 1, 1), ('x', bad, 0)])
    for bad in (-1, 3, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, SU, f, ['a'], [('x', 2, bad)])
        _raises(ValueError, SU, f, ['a'], [('y', 2, 1), ('x', 2, bad)])
    f(['a'], [('x', 1, 0)])
    f(['a'], [('x', 10, 10)])
    _raises(ValueError, CD, f, ['a'], [('x', 1, 1), ('x', 1, 1)])
    _raises(TypeError, TT, f, None, None)
    _raises(ValueError, TS, f, [], None)
    _raises(ValueError, TE, f, [1, 1], None)
    _raises(ValueError, TD, f, ['a', 'a'], None)
    _raises(TypeError, RT, f, ['a'], None)
    _raises(ValueError, RS, f, ['a'], [])
    _raises(ValueError, RE, f, ['a'], [1])
    _raises(ValueError, CX, f, ['a'], [(1, 0, 9)])
    _raises(ValueError, AT, f, ['a'], [('x', 0, 9)])
    _raises(ValueError, SU, f, ['a'], [('x', 1, 9), ('x', 1, 9)])
    _raises(ValueError, CD, f, ['a'], [('x', 1, 1), ('x', 1, 1)])


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
    ("type(taught) not in (list, tuple)", "not isinstance(taught, (list, tuple))"),
    ("not 1 <= len(taught) <= 6", "not 0 <= len(taught) <= 6"),
    ("not 1 <= len(taught) <= 6", "not 1 <= len(taught) < 6"),
    ("not 1 <= len(taught) <= 6", "not 1 <= len(taught) <= 7"),
    ("if len(set(taught)) != len(taught):", "if False:"),
    ("type(trials) not in (list, tuple)", "not isinstance(trials, (list, tuple))"),
    ("not 1 <= len(trials) <= 8", "not 0 <= len(trials) <= 8"),
    ("not 1 <= len(trials) <= 8", "not 1 <= len(trials) < 8"),
    ("not 1 <= len(trials) <= 8", "not 1 <= len(trials) <= 9"),
    ("type(tr) not in (list, tuple) or len(tr) != 3", "not isinstance(tr, (list, tuple)) or len(tr) != 3"),
    ("type(tr) not in (list, tuple) or len(tr) != 3", "type(tr) not in (list, tuple) or len(tr) > 3"),
    ("type(tr) not in (list, tuple) or len(tr) != 3", "type(tr) not in (list, tuple) or len(tr) < 3"),
    ("type(attempts) is not int or not 1 <= attempts <= 10", "not isinstance(attempts, int) or not 1 <= attempts <= 10"),
    ("type(attempts) is not int or not 1 <= attempts <= 10", "isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= 10"),
    ("not 1 <= attempts <= 10", "not 0 <= attempts <= 10"),
    ("not 1 <= attempts <= 10", "not 1 <= attempts < 10"),
    ("not 1 <= attempts <= 10", "not 1 <= attempts <= 11"),
    ("type(successes) is not int or not 0 <= successes <= attempts", "not isinstance(successes, int) or not 0 <= successes <= attempts"),
    ("type(successes) is not int or not 0 <= successes <= attempts", "isinstance(successes, bool) or not isinstance(successes, int) or not 0 <= successes <= attempts"),
    ("not 0 <= successes <= attempts", "not 1 <= successes <= attempts"),
    ("not 0 <= successes <= attempts", "not -1 <= successes <= attempts"),
    ("not 0 <= successes <= attempts", "not 0 <= successes < attempts"),
    ("not 0 <= successes <= attempts", "not 0 <= successes <= attempts + 1"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("if context in taught:", "if context not in taught:"),
    ("old_a += attempts", "old_a += successes"),
    ("new_a += attempts", "new_a += successes"),
    ("new_s += successes", "new_s += attempts"),
    ("new_s * 100 // new_a if new_a else 0", "(new_s * 100 + new_a - 1) // new_a if new_a else 0"),
    ("new_s * 100 // new_a if new_a else 0", "round(new_s * 100 / new_a) if new_a else 0"),
    ("new_s * 100 // new_a if new_a else 0", "new_s * 100 // new_a if new_a else 100"),
    ("new_s >= 1 and new_s * 2 >= new_a", "new_s * 2 >= new_a"),
    ("new_s >= 1 and new_s * 2 >= new_a", "new_s >= 1 and new_s * 2 > new_a"),
    ("new_s >= 1 and new_s * 2 >= new_a", "new_s >= 1 and new_s * 3 >= new_a"),
    ("new_s >= 1 and new_s * 2 >= new_a", "new_s >= 1 and new_s * 2 >= new_a - 1"),
    ("new_s >= 1 and new_s * 2 >= new_a", "new_s >= 1"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
