import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import trunk_branches as mod

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
    assert mod.SCOPE == 'PARTIAL: age and size thresholds over supplied branch records, no repository is read'
    assert len(mod.NOT_CLAIMED) == 5 and 'merge conflicts' in mod.NOT_CLAIMED and 'build health' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(bs, ma):
    st, bg = [], []
    for n, a, c in bs:
        if a - ma > 0:
            st.append(n)
        if c - 20 > 0:
            bg.append(n)
    return {'stale': st, 'big': bg, 'oldest_age': max([a for _, a, _ in bs], default=0), 'ok': len(st) == 0}


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
    f = m.trunk_branches
    assert f([]) == {'stale': [], 'big': [], 'oldest_age': 0, 'ok': True}
    assert f([('a', 0, 0)]) == {'stale': [], 'big': [], 'oldest_age': 0, 'ok': True}
    assert f([('a', 2, 20)]) == {'stale': [], 'big': [], 'oldest_age': 2, 'ok': True}
    assert f([('a', 3, 21)]) == {'stale': ['a'], 'big': ['a'], 'oldest_age': 3, 'ok': False}
    assert f([('a', 3, 0)])['stale'] == ['a'] and f([('a', 1, 21)])['big'] == ['a']
    assert f([('a', 1, 21)])['ok'] is True
    r = f([('x', 5, 1), ('y', 1, 30), ('z', 9, 25), ('w', 2, 2)])
    assert r == {'stale': ['x', 'z'], 'big': ['y', 'z'], 'oldest_age': 9, 'ok': False}
    assert f((['a', 4, 0], ('b', 365, 500)))['oldest_age'] == 365
    assert f([('a', 7, 0), ('b', 3, 0)])['oldest_age'] == 7 and f([('a', 3, 0), ('b', 7, 0)])['oldest_age'] == 7
    assert f([('x' * 16, 0, 0)])['ok'] is True
    # default max_age 2 vs 1 and 3
    assert f([('a', 2, 0)])['ok'] is True and f([('a', 3, 0)])['ok'] is False
    assert f([('a', 2, 0)], 1)['ok'] is False and f([('a', 3, 0)], 3)['ok'] is True and f([('a', 3, 0)], 2) == f([('a', 3, 0)])
    assert f([('a', 14, 0)], 14)['ok'] is True and f([('a', 15, 0)], 14)['ok'] is False
    # default size cap is 12
    r12 = [(chr(97 + i), 0, 0) for i in range(12)]
    f(r12)
    _raises(ValueError, 'branches must contain at most 12 entries', f, r12 + [('m', 0, 0)])
    rng = random.Random(698)
    for _ in range(500):
        bs = [(chr(97 + i), rng.randint(0, 20), rng.randint(0, 30)) for i in range(rng.randint(0, 12))]
        ma = rng.randint(1, 14)
        assert f(bs, ma) == _oracle(bs, ma), (bs, ma)
        assert f(bs) == _oracle(bs, 2)


def _late(m):
    f = m.trunk_branches
    MA = 'max_age must be a nonbool integer between 1 and 14'
    BT = 'branches must be a list or tuple'
    BS = 'branches must contain at most 12 entries'
    BP = 'each branch must be a (name, age_days, commits) triple'
    NM = 'each name must be a string of 1 to 16 characters'
    AG = 'age_days must be a nonbool integer between 0 and 365'
    CM = 'commits must be a nonbool integer between 0 and 500'
    ND = 'names must be distinct'
    for bad in (0, 15, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, MA, f, [], bad)
    f([], 1)
    f([], 14)
    for bad in ('ab', None, 5, {}, L([('a', 1, 1)]), T([('a', 1, 1)]), L(), T()):
        _raises(TypeError, BT, f, bad)
    _raises(ValueError, BS, f, [('a', 1, 1)] * 13)
    for bad in ('ab', None, 5, ('a', 1), ('a', 1, 1, 1), (), {'a': 1}, L(['a', 1, 1]), T(('a', 1, 1))):
        _raises(ValueError, BP, f, [bad])
        _raises(ValueError, BP, f, [('b', 1, 1), bad])
    for bad in ('', 'x' * 17, None, 5, True, S('a'), LyingS('a'), b'a', ['a']):
        _raises(ValueError, NM, f, [(bad, 1, 1)])
        _raises(ValueError, NM, f, [('b', 1, 1), (bad, 1, 1)])
    for bad in (-1, 366, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, AG, f, [('a', bad, 1)])
        _raises(ValueError, AG, f, [('b', 1, 1), ('a', bad, 1)])
    f([('a', 0, 1)])
    f([('a', 365, 1)])
    for bad in (-1, 501, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, CM, f, [('a', 1, bad)])
        _raises(ValueError, CM, f, [('b', 1, 1), ('a', 1, bad)])
    f([('a', 1, 0)])
    f([('a', 1, 500)])
    _raises(ValueError, ND, f, [('a', 1, 1), ('a', 1, 1)])
    _raises(ValueError, ND, f, [('a', 1, 1), ('b', 1, 1), ('a', 2, 2)])
    # validation order
    _raises(ValueError, MA, f, None, I(1))
    _raises(TypeError, BT, f, None)
    _raises(ValueError, BS, f, [1] * 13)
    _raises(ValueError, BP, f, [1])
    _raises(ValueError, NM, f, [(1, -1, -1)])
    _raises(ValueError, AG, f, [('a', -1, -1)])
    _raises(ValueError, CM, f, [('a', 1, -1), ('a', 1, 1)])
    _raises(ValueError, ND, f, [('a', 1, 1), ('a', 1, 1)])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("max_age=2", "max_age=3"),
    ("max_age=2", "max_age=1"),
    ("type(max_age) is not int or not 1 <= max_age <= 14", "not isinstance(max_age, int) or not 1 <= max_age <= 14"),
    ("type(max_age) is not int or not 1 <= max_age <= 14", "isinstance(max_age, bool) or not isinstance(max_age, int) or not 1 <= max_age <= 14"),
    ("not 1 <= max_age <= 14", "not 0 <= max_age <= 14"),
    ("not 1 <= max_age <= 14", "not 1 <= max_age < 14"),
    ("not 1 <= max_age <= 14", "not 1 <= max_age <= 15"),
    ("type(branches) not in (list, tuple)", "not isinstance(branches, (list, tuple))"),
    ("len(branches) > 12", "len(branches) >= 12"),
    ("len(branches) > 12", "len(branches) > 13"),
    ("type(b) not in (list, tuple) or len(b) != 3", "not isinstance(b, (list, tuple)) or len(b) != 3"),
    ("type(b) not in (list, tuple) or len(b) != 3", "type(b) not in (list, tuple) or len(b) > 3"),
    ("type(b) not in (list, tuple) or len(b) != 3", "type(b) not in (list, tuple) or len(b) < 3"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "not isinstance(name, str) or not 1 <= len(name) <= 16"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "type(name) is not str or not 0 <= len(name) <= 16"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "type(name) is not str or not 1 <= len(name) < 16"),
    ("type(name) is not str or not 1 <= len(name) <= 16", "type(name) is not str or not 1 <= len(name) <= 17"),
    ("type(age) is not int or not 0 <= age <= 365", "not isinstance(age, int) or not 0 <= age <= 365"),
    ("type(age) is not int or not 0 <= age <= 365", "isinstance(age, bool) or not isinstance(age, int) or not 0 <= age <= 365"),
    ("not 0 <= age <= 365", "not 1 <= age <= 365"),
    ("not 0 <= age <= 365", "not -1 <= age <= 365"),
    ("not 0 <= age <= 365", "not 0 <= age < 365"),
    ("not 0 <= age <= 365", "not 0 <= age <= 366"),
    ("type(commits) is not int or not 0 <= commits <= 500", "not isinstance(commits, int) or not 0 <= commits <= 500"),
    ("type(commits) is not int or not 0 <= commits <= 500", "isinstance(commits, bool) or not isinstance(commits, int) or not 0 <= commits <= 500"),
    ("not 0 <= commits <= 500", "not 1 <= commits <= 500"),
    ("not 0 <= commits <= 500", "not -1 <= commits <= 500"),
    ("not 0 <= commits <= 500", "not 0 <= commits < 500"),
    ("not 0 <= commits <= 500", "not 0 <= commits <= 501"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("stale = [n for n, a, _ in rows if a > max_age]", "stale = [n for n, a, _ in rows if a >= max_age]"),
    ("stale = [n for n, a, _ in rows if a > max_age]", "stale = [n for n, a, _ in rows if a > max_age + 1]"),
    ("stale = [n for n, a, _ in rows if a > max_age]", "stale = [n for n, a, _ in rows if a > 2]"),
    ("big = [n for n, _, c in rows if c > 20]", "big = [n for n, _, c in rows if c >= 20]"),
    ("big = [n for n, _, c in rows if c > 20]", "big = [n for n, _, c in rows if c > 21]"),
    ("if a > oldest:", "if a >= oldest + 1000:"),
    ("if a > oldest:", "if a < oldest:"),
    ("oldest = 0\n", "oldest = 1\n"),
    ("'ok': not stale", "'ok': not big"),
    ("'ok': not stale", "'ok': not stale and not big"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
