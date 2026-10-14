import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import toggle_rollout as mod

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
    assert mod.SCOPE == 'PARTIAL: modulo-100 percentage rule over supplied toggles and users, no traffic is served'
    assert len(mod.NOT_CLAIMED) == 5 and 'user hashing quality' in mod.NOT_CLAIMED and 'flag service behaviour' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(tg, us):
    out = []
    for n, p in tg:
        on = []
        for u in us:
            bucket = int(str(u)[-2:])
            if bucket < p:
                on.append(u)
        out.append((n, on, len(on)))
    return {'results': out}


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
    f = m.toggle_rollout
    assert f([('a', 50)], []) == {'results': [('a', [], 0)]}
    assert f([('a', 0)], [0, 50, 99]) == {'results': [('a', [], 0)]}
    assert f([('a', 100)], [0, 50, 99]) == {'results': [('a', [0, 50, 99], 3)]}
    assert f([('a', 50)], [49, 50, 150, 149, 99, 0]) == {'results': [('a', [49, 149, 0], 3)]}
    assert f([('a', 1)], [0, 1, 100, 101, 99999, 99900]) == {'results': [('a', [0, 100, 99900], 3)]}
    assert f([('a', 99)], [99, 199, 98])['results'][0][1] == [98]
    r = f((['b', 10], ('a', 100)), (5, 95, 10, 9))
    assert r == {'results': [('b', [5, 9], 2), ('a', [5, 95, 10, 9], 4)]}
    assert f([('x' * 12, 100)], [7])['results'][0][0] == 'x' * 12
    # default max_users is 10
    f([('a', 1)], [1] * 10)
    _raises(ValueError, 'users must contain at most max_users entries', f, [('a', 1)], [1] * 11)
    assert f([('a', 100)], [1] * 11, 11)['results'][0][2] == 11
    assert f([('a', 100)], [1] * 50, 50)['results'][0][2] == 50
    _raises(ValueError, 'users must contain at most max_users entries', f, [('a', 1)], [1] * 3, 2)
    f([('a', 1)], [1] * 2, 2)
    assert len(f([(chr(97 + i), 1) for i in range(8)], [])['results']) == 8
    rng = random.Random(697)
    for _ in range(400):
        tg = [(chr(97 + i), rng.randint(0, 100)) for i in range(rng.randint(1, 8))]
        us = [rng.choice((rng.randint(0, 99999), rng.randint(0, 200))) for _ in range(rng.randint(0, 10))]
        assert f(tg, us) == _oracle(tg, us), (tg, us)
    for p in range(0, 101):
        got = f([('a', p)], list(range(50)), 50)['results'][0]
        assert got[2] == min(p, 50)


def _late(m):
    f = m.toggle_rollout
    MU = 'max_users must be a nonbool integer between 1 and 50'
    TT = 'toggles must be a list or tuple'
    TS = 'toggles must contain 1 to 8 entries'
    TP = 'each toggle must be a (name, percent) pair'
    NM = 'each name must be a string of 1 to 12 characters'
    PC = 'percent must be a nonbool integer between 0 and 100'
    ND = 'names must be distinct'
    UT = 'users must be a list or tuple'
    US = 'users must contain at most max_users entries'
    UE = 'each user must be a nonbool integer between 0 and 99999'
    ok = [('a', 1)]
    for bad in (0, 51, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MU, f, ok, [], bad)
    f(ok, [], 1)
    f(ok, [], 50)
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, TT, f, bad, [])
    _raises(ValueError, TS, f, [], [])
    _raises(ValueError, TS, f, [(chr(97 + i), 1) for i in range(9)], [])
    f([(chr(97 + i), 1) for i in range(8)], [])
    for bad in ('ab', None, 5, ('a',), ('a', 1, 1), (), {'a': 1}, L(['a', 1]), T(('a', 1))):
        _raises(ValueError, TP, f, [bad], [])
        _raises(ValueError, TP, f, [('b', 1), bad], [])
    for bad in ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a']):
        _raises(ValueError, NM, f, [(bad, 1)], [])
        _raises(ValueError, NM, f, [('b', 1), (bad, 1)], [])
    for bad in (-1, 101, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, PC, f, [('a', bad)], [])
        _raises(ValueError, PC, f, [('b', 1), ('a', bad)], [])
    f([('a', 0)], [])
    f([('a', 100)], [])
    _raises(ValueError, ND, f, [('a', 1), ('a', 2)], [])
    _raises(ValueError, ND, f, [('a', 1), ('b', 2), ('a', 2)], [])
    for bad in ('ab', None, 5, {}, L([1]), T([1]), L(), T()):
        _raises(TypeError, UT, f, ok, bad)
    _raises(ValueError, US, f, ok, [1] * 11)
    for bad in (-1, 100000, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30), 10 ** 30):
        _raises(ValueError, UE, f, ok, [bad])
        _raises(ValueError, UE, f, ok, [1, bad])
    f(ok, [0, 99999])
    # validation order
    _raises(ValueError, MU, f, None, None, I(1))
    _raises(TypeError, TT, f, None, None)
    _raises(ValueError, TS, f, [], None)
    _raises(ValueError, TP, f, [1], None)
    _raises(ValueError, NM, f, [(1, 1)], None)
    _raises(ValueError, PC, f, [('a', 101), ('a', 1)], None)
    _raises(ValueError, ND, f, [('a', 1), ('a', 1)], None)
    _raises(TypeError, UT, f, ok, None)
    _raises(ValueError, US, f, ok, [True] * 11)
    _raises(ValueError, UE, f, ok, [True])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_users=10", "max_users=11"),
    ("max_users=10", "max_users=9"),
    ("type(max_users) is not int or not 1 <= max_users <= 50", "not isinstance(max_users, int) or not 1 <= max_users <= 50"),
    ("type(max_users) is not int or not 1 <= max_users <= 50", "isinstance(max_users, bool) or not isinstance(max_users, int) or not 1 <= max_users <= 50"),
    ("not 1 <= max_users <= 50", "not 0 <= max_users <= 50"),
    ("not 1 <= max_users <= 50", "not 1 <= max_users < 50"),
    ("not 1 <= max_users <= 50", "not 1 <= max_users <= 51"),
    ("type(toggles) not in (list, tuple)", "not isinstance(toggles, (list, tuple))"),
    ("not 1 <= len(toggles) <= 8", "not 0 <= len(toggles) <= 8"),
    ("not 1 <= len(toggles) <= 8", "not 1 <= len(toggles) < 8"),
    ("not 1 <= len(toggles) <= 8", "not 1 <= len(toggles) <= 9"),
    ("type(t) not in (list, tuple) or len(t) != 2", "not isinstance(t, (list, tuple)) or len(t) != 2"),
    ("type(t) not in (list, tuple) or len(t) != 2", "type(t) not in (list, tuple) or len(t) > 2"),
    ("type(t) not in (list, tuple) or len(t) != 2", "type(t) not in (list, tuple) or len(t) < 2"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "not isinstance(name, str) or not 1 <= len(name) <= 12"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "type(name) is not str or not 0 <= len(name) <= 12"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "type(name) is not str or not 1 <= len(name) < 12"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "type(name) is not str or not 1 <= len(name) <= 13"),
    ("type(pct) is not int or not 0 <= pct <= 100", "not isinstance(pct, int) or not 0 <= pct <= 100"),
    ("type(pct) is not int or not 0 <= pct <= 100", "isinstance(pct, bool) or not isinstance(pct, int) or not 0 <= pct <= 100"),
    ("not 0 <= pct <= 100", "not 1 <= pct <= 100"),
    ("not 0 <= pct <= 100", "not 0 <= pct < 100"),
    ("not 0 <= pct <= 100", "not 0 <= pct <= 101"),
    ("not 0 <= pct <= 100", "not -1 <= pct <= 100"),
    ("len({n for n, _ in rows}) != len(rows)", "False"),
    ("type(users) not in (list, tuple)", "not isinstance(users, (list, tuple))"),
    ("len(users) > max_users", "len(users) >= max_users"),
    ("type(u) is not int or not 0 <= u <= 99999", "not isinstance(u, int) or not 0 <= u <= 99999"),
    ("type(u) is not int or not 0 <= u <= 99999", "isinstance(u, bool) or not isinstance(u, int) or not 0 <= u <= 99999"),
    ("not 0 <= u <= 99999", "not 1 <= u <= 99999"),
    ("not 0 <= u <= 99999", "not -1 <= u <= 99999"),
    ("not 0 <= u <= 99999", "not 0 <= u < 99999"),
    ("not 0 <= u <= 99999", "not 0 <= u <= 100000"),
    ("u % 100 < pct", "u % 100 <= pct"),
    ("u % 100 < pct", "u % 10 < pct"),
    ("u % 100 < pct", "u < pct"),
    ("u % 100 < pct", "u % 100 > pct"),
    ("u % 100 < pct", "(u // 100) % 100 < pct"),
    ("results.append((name, on, len(on)))", "results.append((name, on, len(on) + 1))"),
    ("results.append((name, on, len(on)))", "results.append((name, sorted(on, reverse=True), len(on)))"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
