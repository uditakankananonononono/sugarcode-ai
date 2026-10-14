import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import canary_cohort_split as mod

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
    assert mod.SCOPE == 'PARTIAL: fixed code-point-sum bucketing of supplied user names, no real traffic'
    assert len(mod.NOT_CLAIMED) >= 4 and 'real traffic' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _bucket(name):
    """Independent: add the code points one by one with divmod, no sum()."""
    total = 0
    for ch in name:
        total += ord(ch)
    return divmod(total, 100)[1]


def _core(m):
    # hand literals: 'a'=97 'b'=98 'ab'=195->95 'ba'=95 'z'=122->22 '\u20ac'=8364->64 'e\u0301'=101+769=870->70
    assert m.split_cohorts(['a', 'b', 'ab', 'z'], 50) == {'canary': ['z'], 'control': ['a', 'ab', 'b'], 'buckets': {'a': 97, 'b': 98, 'ab': 95, 'z': 22}}
    assert m.split_cohorts(['\u20ac', 'e\u0301'], 65)['canary'] == ['\u20ac']
    assert m.split_cohorts(['\u20ac', 'e\u0301'], 65)['buckets'] == {'\u20ac': 64, 'e\u0301': 70}
    assert m.split_cohorts([], 100) == {'canary': [], 'control': [], 'buckets': {}}
    # percent edges: 0 puts nobody in the canary, 100 puts everybody, one off either side moves exactly the edge user
    assert m.split_cohorts(['a', 'z'], 0) == {'canary': [], 'control': ['a', 'z'], 'buckets': {'a': 97, 'z': 22}}
    assert m.split_cohorts(['a', 'z'], 100)['canary'] == ['a', 'z']
    assert m.split_cohorts(['a', 'z'], 22)['canary'] == []
    assert m.split_cohorts(['a', 'z'], 23)['canary'] == ['z']
    assert m.split_cohorts(['a', 'z'], 97)['canary'] == ['z']
    assert m.split_cohorts(['a', 'z'], 98)['canary'] == ['a', 'z']
    # default percent is 10: buckets 9 ('\t'), 10 ('\n'), 11 and 99
    edge = ['\t', '\n', '\x0b', 'c']
    assert m.split_cohorts(edge)['canary'] == ['\t']
    assert m.split_cohorts(edge, 10) == m.split_cohorts(edge)
    assert m.split_cohorts(tuple(edge), 11)['canary'] == ['\t', '\n']
    assert m.split_cohorts(['x' * 16], 100)['canary'] == ['x' * 16]
    assert m.split_cohorts(['n%d' % i for i in range(50)], 100)['canary'] == sorted('n%d' % i for i in range(50))
    rng = random.Random(624)
    for _ in range(300):
        names = list({''.join(rng.choice('abcxyz012\u00e9') for _ in range(rng.randint(1, 5))) for _ in range(rng.randint(0, 12))})
        p = rng.randint(0, 100)
        r = m.split_cohorts(names, p)
        assert r['buckets'] == {n: _bucket(n) for n in names}
        assert r['canary'] == sorted(n for n in names if _bucket(n) < p)
        assert r['control'] == sorted(n for n in names if _bucket(n) >= p)
        assert len(r['canary']) + len(r['control']) == len(names)
        assert set(r['canary']) <= set(m.split_cohorts(names, min(100, p + 1))['canary'])   # raising the percent only adds


def _late(m):
    US = 'users must be a list or tuple'
    PC = 'percent must be a nonbool integer between 0 and 100'
    NM = 'user names must be unique strings of 1 to 16 characters'
    for bad in ('ab', None, 5, {}, L(['a']), T(['a']), L(), T()):
        _raises(TypeError, US, m.split_cohorts, bad)
    _raises(TypeError, US, m.split_cohorts, L(['a'] * 51))
    _raises(ValueError, 'users must contain at most 50 entries', m.split_cohorts, ['n%d' % i for i in range(51)])
    for bad in (-1, 101, True, False, 1.0, '1', None, I(10), LyingI(10), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, PC, m.split_cohorts, ['a'], bad)
    for bad in ('', 'x' * 17, None, 5, b'a', S('a'), LyingS('a'), ['a']):
        _raises(ValueError, NM, m.split_cohorts, [bad])
        _raises(ValueError, NM, m.split_cohorts, ['ok', bad])
    _raises(ValueError, NM, m.split_cohorts, ['a', 'b', 'a'])
    _raises(ValueError, NM, m.split_cohorts, ['a', S('b'), 'a'])
    _raises(TypeError, US, m.split_cohorts, L([S('a')]), I(1))
    _raises(ValueError, 'users must contain at most 50 entries', m.split_cohorts, ['n%d' % i for i in range(51)], I(1))
    _raises(ValueError, PC, m.split_cohorts, [S('a')], I(1))


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


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_users_unchanged():
    users = ['b', 'a']
    r = mod.split_cohorts(users, 100)
    r['canary'].append('x')
    r['buckets']['zzz'] = 1
    assert users == ['b', 'a']
    assert mod.split_cohorts(users, 100)['canary'] == ['a', 'b']


MUTANTS = [
    ("type(users) not in (list, tuple)", "not isinstance(users, (list, tuple))"),
    ("len(users) > MAX_USERS", "len(users) >= MAX_USERS"),
    ("MAX_USERS = 50", "MAX_USERS = 51"),
    ("type(percent) is not int or not 0 <= percent <= 100", "isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100"),
    ("type(percent) is not int or not 0 <= percent <= 100", "not isinstance(percent, int) or not 0 <= percent <= 100"),
    ("not 0 <= percent <= 100", "not 1 <= percent <= 100"),
    ("not 0 <= percent <= 100", "not 0 <= percent < 100"),
    ("not 0 <= percent <= 100", "not 0 <= percent <= 101"),
    ("percent=10", "percent=11"),
    ("percent=10", "percent=9"),
    ("type(u) is not str", "not isinstance(u, str)"),
    ("not 1 <= len(u) <= 16", "not 0 <= len(u) <= 16"),
    ("not 1 <= len(u) <= 16", "not 1 <= len(u) <= 17"),
    ("not 1 <= len(u) <= 16", "not 1 <= len(u) < 16"),
    ("len(set(users)) != len(users)", "False"),
    ("sum(ord(c) for c in u) % 100", "sum(ord(c) for c in u) % 101"),
    ("sum(ord(c) for c in u) % 100", "sum(ord(c) for c in u) % 10"),
    ("sum(ord(c) for c in u) % 100", "sum(ord(c) for c in u[:1]) % 100"),
    ("sum(ord(c) for c in u) % 100", "(sum(ord(c) for c in u) + 1) % 100"),
    ("sum(ord(c) for c in u) % 100", "sum(ord(c) & 255 for c in u) % 100"),
    ("buckets[u] < percent)", "buckets[u] <= percent)"),
    ("buckets[u] >= percent)", "buckets[u] > percent)"),
    ("'canary': sorted(", "'canary': list("),
    ("'control': sorted(", "'control': list("),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
