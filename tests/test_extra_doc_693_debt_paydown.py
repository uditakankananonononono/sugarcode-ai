import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import debt_paydown as mod

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
    assert mod.SCOPE == 'PARTIAL: greedy interest-per-cost ranking of supplied debt items, no code is measured'
    assert len(mod.NOT_CLAIMED) == 5 and 'optimal packing' in mod.NOT_CLAIMED and 'true interest rates' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(items, cap):
    """Independent: stable sorted with Fraction keys."""
    from fractions import Fraction
    rk = sorted(items, key=lambda t: -Fraction(t[2], t[1]))
    paid, sk, used, sv, rem = [], [], 0, 0, 0
    for n, c, i in rk:
        if used + c <= cap:
            used += c
            paid.append(n)
            sv += i
        else:
            sk.append(n)
            rem += i
    return {'paid': paid, 'skipped': sk, 'spent': used, 'saved': sv, 'remaining': rem}


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
    f = m.debt_paydown
    assert f([]) == {'paid': [], 'skipped': [], 'spent': 0, 'saved': 0, 'remaining': 0}
    assert f([('a', 5, 3)]) == {'paid': ['a'], 'skipped': [], 'spent': 5, 'saved': 3, 'remaining': 0}
    assert f([('a', 21, 3)]) == {'paid': [], 'skipped': ['a'], 'spent': 0, 'saved': 0, 'remaining': 3}
    assert f([('a', 20, 0)])['paid'] == ['a']
    # ranking by ratio: b 6/2=3, a 4/2=2, c 3/3=1
    r = f([('a', 2, 4), ('b', 2, 6), ('c', 3, 3)])
    assert r['paid'] == ['b', 'a', 'c'] and r['spent'] == 7 and r['saved'] == 13
    # equal ratios keep input order
    assert f([('a', 2, 2), ('b', 4, 4), ('c', 1, 1)])['paid'] == ['a', 'b', 'c']
    assert f([('c', 1, 1), ('b', 4, 4), ('a', 2, 2)])['paid'] == ['c', 'b', 'a']
    # skipped item does not stop later cheaper ones
    r = f([('big', 15, 45), ('mid', 10, 20), ('small', 4, 4)])
    assert r == {'paid': ['big', 'small'], 'skipped': ['mid'], 'spent': 19, 'saved': 49, 'remaining': 20}
    # default capacity 20 differs from 19 and 21
    assert f([('a', 20, 1)])['paid'] == ['a'] and f([('a', 20, 1)], 19)['paid'] == [] and f([('a', 21, 1)], 21)['paid'] == ['a']
    assert f([('a', 20, 1)], 20) == f((('a', 20, 1),))
    assert f([('a', 100, 50)], 200)['spent'] == 100 and f([('a', 100, 50)], 1)['skipped'] == ['a']
    assert f([('a', 100, 50)], 99)['skipped'] == ['a'] and f([('a', 100, 50)], 100)['paid'] == ['a']
    assert f([['a', 5, 3]])['paid'] == ['a']
    # exact ratio compare, not float-rounded or integer division: 1/3 vs 33/100 differs, 7/3 vs 2
    assert f([('a', 3, 1), ('b', 100, 33)], 103)['paid'] == ['a', 'b']
    assert f([('b', 100, 33), ('a', 3, 1)], 103)['paid'] == ['a', 'b']
    assert f([('a', 3, 7), ('b', 1, 2)])['paid'] == ['a', 'b']
    assert f([('b', 1, 2), ('a', 3, 7)])['paid'] == ['a', 'b']
    assert f([('a', 1, 0), ('b', 1, 1)])['paid'] == ['b', 'a']
    rng = random.Random(693)
    for _ in range(500):
        n = rng.randint(0, 12)
        its = [(chr(97 + i), rng.randint(1, 12), rng.randint(0, 12)) for i in range(n)]
        cap = rng.choice((20, rng.randint(1, 60)))
        got = f(its, cap) if cap != 20 or rng.random() < 0.5 else f(its)
        assert got == _oracle(its, cap), (its, cap)


def _late(m):
    f = m.debt_paydown
    CP = 'capacity must be a nonbool integer between 1 and 200'
    IT = 'items must be a list or tuple'
    IS = 'items must contain at most 12 entries'
    IP = 'each item must be a (name, cost, interest) triple'
    NM = 'each name must be a string of 1 to 12 characters'
    CO = 'cost must be a nonbool integer between 1 and 100'
    IN = 'interest must be a nonbool integer between 0 and 50'
    ND = 'names must be distinct'
    for bad in (0, 201, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, CP, f, [], bad)
    f([], 1)
    f([], 200)
    for bad in ('ab', None, 5, {}, L([('a', 1, 1)]), T([('a', 1, 1)]), L(), T()):
        _raises(TypeError, IT, f, bad)
    _raises(ValueError, IS, f, [('a', 1, 1)] * 13)
    f([(chr(97 + i), 1, 1) for i in range(12)])
    for bad in ('ab', None, 5, ('a', 1), ('a', 1, 1, 1), (), {'a': 1}, L(['a', 1, 1]), T(('a', 1, 1))):
        _raises(ValueError, IP, f, [bad])
        _raises(ValueError, IP, f, [('b', 1, 1), bad])
    for bad in ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a']):
        _raises(ValueError, NM, f, [(bad, 1, 1)])
        _raises(ValueError, NM, f, [('b', 1, 1), (bad, 1, 1)])
    f([('x' * 12, 1, 1)])
    for bad in (0, 101, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, CO, f, [('a', bad, 1)])
        _raises(ValueError, CO, f, [('b', 1, 1), ('a', bad, 1)])
    f([('a', 1, 1)])
    f([('a', 100, 1)], 100)
    for bad in (-1, 51, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, IN, f, [('a', 1, bad)])
        _raises(ValueError, IN, f, [('b', 1, 1), ('a', 1, bad)])
    f([('a', 1, 0)])
    f([('a', 1, 50)])
    _raises(ValueError, ND, f, [('a', 1, 1), ('a', 1, 1)])
    _raises(ValueError, ND, f, [('a', 1, 1), ('b', 1, 1), ('a', 2, 2)])
    # validation order
    _raises(ValueError, CP, f, None, I(1))
    _raises(TypeError, IT, f, None)
    _raises(ValueError, IS, f, [1] * 13)
    _raises(ValueError, IP, f, [1, 1, 1])
    _raises(ValueError, NM, f, [(1, 0, -1)])
    _raises(ValueError, CO, f, [('a', 0, -1)])
    _raises(ValueError, IN, f, [('a', 1, -1), ('a', 1, 1)])
    _raises(ValueError, ND, f, [('a', 1, 1), ('a', 1, 1)])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ("capacity=20", "capacity=21"),
    ("capacity=20", "capacity=19"),
    ("type(capacity) is not int or not 1 <= capacity <= 200", "not isinstance(capacity, int) or not 1 <= capacity <= 200"),
    ("type(capacity) is not int or not 1 <= capacity <= 200", "isinstance(capacity, bool) or not isinstance(capacity, int) or not 1 <= capacity <= 200"),
    ("not 1 <= capacity <= 200", "not 0 <= capacity <= 200"),
    ("not 1 <= capacity <= 200", "not 1 <= capacity < 200"),
    ("not 1 <= capacity <= 200", "not 1 <= capacity <= 201"),
    ("type(items) not in (list, tuple)", "not isinstance(items, (list, tuple))"),
    ("len(items) > 12", "len(items) >= 12"),
    ("len(items) > 12", "len(items) > 13"),
    ("type(t) not in (list, tuple) or len(t) != 3", "not isinstance(t, (list, tuple)) or len(t) != 3"),
    ("type(t) not in (list, tuple) or len(t) != 3", "type(t) not in (list, tuple) or len(t) > 3"),
    ("type(t) not in (list, tuple) or len(t) != 3", "type(t) not in (list, tuple) or len(t) < 3"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "not isinstance(name, str) or not 1 <= len(name) <= 12"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "type(name) is not str or not 0 <= len(name) <= 12"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "type(name) is not str or not 1 <= len(name) < 12"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "type(name) is not str or not 1 <= len(name) <= 13"),
    ("type(cost) is not int or not 1 <= cost <= 100", "not isinstance(cost, int) or not 1 <= cost <= 100"),
    ("type(cost) is not int or not 1 <= cost <= 100", "isinstance(cost, bool) or not isinstance(cost, int) or not 1 <= cost <= 100"),
    ("not 1 <= cost <= 100", "not 0 <= cost <= 100"),
    ("not 1 <= cost <= 100", "not 1 <= cost < 100"),
    ("not 1 <= cost <= 100", "not 1 <= cost <= 101"),
    ("type(interest) is not int or not 0 <= interest <= 50", "not isinstance(interest, int) or not 0 <= interest <= 50"),
    ("type(interest) is not int or not 0 <= interest <= 50", "isinstance(interest, bool) or not isinstance(interest, int) or not 0 <= interest <= 50"),
    ("not 0 <= interest <= 50", "not 1 <= interest <= 50"),
    ("not 0 <= interest <= 50", "not -1 <= interest <= 50"),
    ("not 0 <= interest <= 50", "not 0 <= interest < 50"),
    ("not 0 <= interest <= 50", "not 0 <= interest <= 51"),
    ("len({r[0] for r in rows}) != len(rows)", "False"),
    ("order[j][2] * cur[1] < cur[2] * order[j][1]", "order[j][2] * cur[1] <= cur[2] * order[j][1]"),
    ("order[j][2] * cur[1] < cur[2] * order[j][1]", "order[j][2] * cur[1] > cur[2] * order[j][1]"),
    ("order[j][2] * cur[1] < cur[2] * order[j][1]", "order[j][2] // order[j][1] < cur[2] // cur[1]"),
    ("order[j][2] * cur[1] < cur[2] * order[j][1]", "order[j][2] < cur[2]"),
    ("order[j][2] * cur[1] < cur[2] * order[j][1]", "order[j][1] > cur[1]"),
    ("if cost <= left:", "if cost < left:"),
    ("if cost <= left:", "if cost <= capacity:"),
    ("left -= cost", "left -= 1"),
    ("saved += interest", "saved += cost"),
    ("remaining += interest", "remaining += cost"),
    ("'spent': capacity - left", "'spent': left"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
