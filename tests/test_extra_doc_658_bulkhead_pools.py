import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import bulkhead_pools as mod

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
    assert mod.SCOPE == 'PARTIAL: pool admission arithmetic over supplied requests, no real concurrency'
    assert len(mod.NOT_CLAIMED) >= 4 and 'queueing' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(pools, reqs, tot):
    """Independent: per-request counting of earlier admissions."""
    lim = dict(pools)
    st = []
    for i, r in enumerate(reqs):
        ad_pool = sum(1 for j in range(i) if st[j] == 'admitted' and reqs[j] == r)
        ad_all = sum(1 for j in range(i) if st[j] == 'admitted')
        if ad_pool >= lim[r]:
            st.append('pool_full')
        elif tot is not None and ad_all >= tot:
            st.append('total_full')
        else:
            st.append('admitted')
    return {'statuses': st,
            'in_flight': {n: sum(1 for i, r in enumerate(reqs) if r == n and st[i] == 'admitted') for n, _ in pools},
            'rejected': {n: sum(1 for i, r in enumerate(reqs) if r == n and st[i] != 'admitted') for n, _ in pools}}


def _core(m):
    P = [('db', 2), ('api', 3)]
    r = m.bulkhead_pools(P, [])
    assert r == {'statuses': [], 'in_flight': {'db': 0, 'api': 0}, 'rejected': {'db': 0, 'api': 0}} and list(r['in_flight']) == ['db', 'api']
    r = m.bulkhead_pools(P, ['db', 'db', 'db', 'api', 'db', 'api'])
    assert r == {'statuses': ['admitted', 'admitted', 'pool_full', 'admitted', 'pool_full', 'admitted'],
                 'in_flight': {'db': 2, 'api': 2}, 'rejected': {'db': 2, 'api': 0}}
    # a full pool does not stop another pool
    assert m.bulkhead_pools(P, ['db'] * 5 + ['api'])['statuses'][-1] == 'admitted'
    # shared cap
    r = m.bulkhead_pools(P, ['db', 'api', 'api', 'api', 'db'], 3)
    assert r['statuses'] == ['admitted', 'admitted', 'admitted', 'total_full', 'total_full']
    assert r['in_flight'] == {'db': 1, 'api': 2} and r['rejected'] == {'db': 1, 'api': 1}
    assert m.bulkhead_pools(P, ['db', 'api', 'api', 'api', 'db'], None) == m.bulkhead_pools(P, ['db', 'api', 'api', 'api', 'db'])
    assert m.bulkhead_pools(P, ['db', 'api', 'api', 'api', 'db'])['statuses'] == ['admitted'] * 5      # no shared cap by default
    # pool_full wins over total_full
    assert m.bulkhead_pools([('a', 1)], ['a', 'a'], 1)['statuses'] == ['admitted', 'pool_full']
    assert m.bulkhead_pools([('a', 2), ('b', 2)], ['a', 'b', 'a'], 2)['statuses'] == ['admitted', 'admitted', 'total_full']
    assert m.bulkhead_pools([('a', 1)], ['a'], 1)['statuses'] == ['admitted']
    assert m.bulkhead_pools((('a', 10),), ['a'] * 11)['in_flight'] == {'a': 10}
    assert m.bulkhead_pools([['a', 10]], ['a'] * 11)['statuses'][-1] == 'pool_full'
    six = [('p%d' % i, 10) for i in range(6)]
    assert m.bulkhead_pools(six, ['p%d' % (i % 6) for i in range(40)], 60)['statuses'] == ['admitted'] * 40
    assert m.bulkhead_pools(six, ['p%d' % (i % 6) for i in range(40)], 1)['statuses'] == ['admitted'] + ['total_full'] * 39
    assert m.bulkhead_pools([('n' * 12, 1)], ['n' * 12])['in_flight'] == {'n' * 12: 1}
    rng = random.Random(658)
    for _ in range(500):
        k = rng.randint(1, 6)
        pools = [('p%d' % i, rng.randint(1, 10)) for i in range(k)]
        reqs = ['p%d' % rng.randrange(k) for _ in range(rng.randint(0, 40))]
        tot = rng.choice([None, 1, 5, 12, 60])
        assert m.bulkhead_pools(pools, reqs, tot) == _oracle(pools, reqs, tot), (pools, reqs, tot)
        assert m.bulkhead_pools(pools, reqs) == _oracle(pools, reqs, None)


def _late(m):
    PL = 'pools must be a list or tuple'
    PS = 'pools must contain 1 to 6 entries'
    RQ = 'requests must be a list or tuple'
    RS = 'requests must contain at most 40 entries'
    TL = 'total_limit must be None or a nonbool integer between 1 and 60'
    PR = 'each pool must be a (name, limit) pair'
    NM = 'pool names must be strings of 1 to 12 characters'
    DN = 'duplicate pool name'
    LM = 'limit must be a nonbool integer between 1 and 10'
    KP = 'each request must name a known pool'
    ok = ('a', 1)
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, PL, m.bulkhead_pools, bad, [])
    _raises(TypeError, PL, m.bulkhead_pools, L([ok] * 7), [])
    _raises(ValueError, PS, m.bulkhead_pools, [], [])
    _raises(ValueError, PS, m.bulkhead_pools, [ok] * 7, [])
    assert m.bulkhead_pools([('p%d' % i, 1) for i in range(6)], [])['in_flight']['p5'] == 0
    for bad in ('ab', None, 5, {}, L(['a']), T(['a']), L(), T()):
        _raises(TypeError, RQ, m.bulkhead_pools, [ok], bad)
    _raises(TypeError, RQ, m.bulkhead_pools, [ok], L(['a'] * 41))
    _raises(ValueError, RS, m.bulkhead_pools, [ok], ['a'] * 41)
    assert m.bulkhead_pools([('a', 10)], ['a'] * 40)['in_flight'] == {'a': 10}
    for bad in (0, 61, -1, True, False, 1.0, '1', I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TL, m.bulkhead_pools, [ok], [], bad)
    assert m.bulkhead_pools([ok], [], 1) and m.bulkhead_pools([ok], [], 60)
    for K in (L, T):
        for bad in (K(ok), K(('a',))):
            _raises(ValueError, PR, m.bulkhead_pools, [bad], [])
            _raises(ValueError, PR, m.bulkhead_pools, [ok, bad], [])
    for bad in ('ab', None, 5, ('a',), ('a', 1, 1), ()):
        _raises(ValueError, PR, m.bulkhead_pools, [bad], [])
        _raises(ValueError, PR, m.bulkhead_pools, [ok, bad], [])
    for bad in ('', 'x' * 13, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, NM, m.bulkhead_pools, [(bad, 1)], [])
        _raises(ValueError, NM, m.bulkhead_pools, [ok, (bad, 1)], [])
    _raises(ValueError, DN, m.bulkhead_pools, [ok, ('a', 2)], [])
    _raises(ValueError, DN, m.bulkhead_pools, [ok, ('b', 1), ('a', 1)], [])
    for bad in (0, 11, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, LM, m.bulkhead_pools, [('b', bad)], [])
        _raises(ValueError, LM, m.bulkhead_pools, [ok, ('b', bad)], [])
    for bad in ('', 'zz', None, 5, S('a'), LyingS('a'), b'a', ['a']):
        _raises(ValueError, KP, m.bulkhead_pools, [ok], [bad])
        _raises(ValueError, KP, m.bulkhead_pools, [ok], ['a', bad])
    # order: pools type, pools size, requests type, requests size, total_limit, pools rows, requests
    _raises(TypeError, PL, m.bulkhead_pools, L([1]), L([1]), I(1))
    _raises(ValueError, PS, m.bulkhead_pools, [], L([1]), I(1))
    _raises(TypeError, RQ, m.bulkhead_pools, [1], L([1]), I(1))
    _raises(ValueError, RS, m.bulkhead_pools, [1], [1] * 41, I(1))
    _raises(ValueError, TL, m.bulkhead_pools, [1], [1], I(1))
    _raises(ValueError, PR, m.bulkhead_pools, [1], [1], 5)
    _raises(ValueError, NM, m.bulkhead_pools, [(5, I(1))], [1])
    _raises(ValueError, DN, m.bulkhead_pools, [ok, ('a', I(1))], [1])
    _raises(ValueError, LM, m.bulkhead_pools, [('b', I(1))], [1])
    _raises(ValueError, KP, m.bulkhead_pools, [ok], [1])


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


MUTANTS = [
    ("type(pools) not in (list, tuple)", "not isinstance(pools, (list, tuple))"),
    ("not 1 <= len(pools) <= 6", "not 0 <= len(pools) <= 6"),
    ("not 1 <= len(pools) <= 6", "not 1 <= len(pools) < 6"),
    ("not 1 <= len(pools) <= 6", "not 1 <= len(pools) <= 7"),
    ("type(requests) not in (list, tuple)", "not isinstance(requests, (list, tuple))"),
    ("len(requests) > 40", "len(requests) >= 40"),
    ("len(requests) > 40", "len(requests) > 41"),
    ("total_limit=None", "total_limit=1"),
    ("total_limit is not None and (type(total_limit) is not int or not 1 <= total_limit <= 60)", "total_limit is not None and (not isinstance(total_limit, int) or not 1 <= total_limit <= 60)"),
    ("type(total_limit) is not int or not 1 <= total_limit <= 60", "isinstance(total_limit, bool) or not isinstance(total_limit, int) or not 1 <= total_limit <= 60"),
    ("not 1 <= total_limit <= 60", "not 0 <= total_limit <= 60"),
    ("not 1 <= total_limit <= 60", "not 1 <= total_limit < 60"),
    ("not 1 <= total_limit <= 60", "not 1 <= total_limit <= 61"),
    ("type(p) not in (list, tuple) or len(p) != 2", "not isinstance(p, (list, tuple)) or len(p) != 2"),
    ("or len(p) != 2", "or len(p) > 2"),
    ("or len(p) != 2", "or len(p) < 2"),
    ("type(name) is not str or not 1 <= len(name) <= 12", "not isinstance(name, str) or not 1 <= len(name) <= 12"),
    ("not 1 <= len(name) <= 12", "not 0 <= len(name) <= 12"),
    ("not 1 <= len(name) <= 12", "not 1 <= len(name) < 12"),
    ("not 1 <= len(name) <= 12", "not 1 <= len(name) <= 13"),
    ("if name in limits:", "if False:"),
    ("type(limit) is not int or not 1 <= limit <= 10", "not isinstance(limit, int) or not 1 <= limit <= 10"),
    ("type(limit) is not int or not 1 <= limit <= 10", "isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10"),
    ("not 1 <= limit <= 10", "not 0 <= limit <= 10"),
    ("not 1 <= limit <= 10", "not 1 <= limit < 10"),
    ("not 1 <= limit <= 10", "not 1 <= limit <= 11"),
    ("type(r) is not str or r not in limits", "not isinstance(r, str) or r not in limits"),
    ("if in_flight[r] >= limits[r]:", "if in_flight[r] > limits[r]:"),
    ("elif total_limit is not None and total >= total_limit:", "elif total_limit is not None and total > total_limit:"),
    ("elif total_limit is not None and total >= total_limit:", "elif total >= 3:"),
    ("in_flight[r] += 1", "in_flight[r] += 2"),
    ("total += 1", "pass"),
    ("rejected[r] += 1\n        elif", "pass\n        elif"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
