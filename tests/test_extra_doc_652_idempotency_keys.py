import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import idempotency_keys as mod

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
    assert mod.SCOPE == 'PARTIAL: replay and conflict handling of supplied keyed requests, no real storage'
    assert len(mod.NOT_CLAIMED) >= 4 and 'concurrency' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(reqs, cap):
    """Independent: a list of [key, payload] pairs, oldest first."""
    mem, st = [], []
    for k, p in reqs:
        hit = [e for e in mem if e[0] == k]
        if hit:
            st.append('replayed' if hit[0][1] == p else 'conflict')
            continue
        st.append('executed')
        mem.append([k, p])
        while len(mem) > cap:
            mem.pop(0)
    return {'statuses': st, 'counts': {'executed': st.count('executed'), 'replayed': st.count('replayed'), 'conflict': st.count('conflict')},
            'remembered': [e[0] for e in mem]}


def _core(m):
    assert m.idempotency_keys([]) == {'statuses': [], 'counts': {'executed': 0, 'replayed': 0, 'conflict': 0}, 'remembered': []}
    r = m.idempotency_keys([('a', 1), ('a', 1), ('a', 2), ('b', 0)])
    assert r == {'statuses': ['executed', 'replayed', 'conflict', 'executed'], 'counts': {'executed': 2, 'replayed': 1, 'conflict': 1}, 'remembered': ['a', 'b']}
    assert list(r['counts']) == ['executed', 'replayed', 'conflict']
    # default capacity 5: the sixth distinct key evicts the first, which then executes again
    six = [('k%d' % i, i) for i in range(6)]
    r = m.idempotency_keys(six + [('k0', 0)])
    assert r['statuses'] == ['executed'] * 7 and r['remembered'] == ['k2', 'k3', 'k4', 'k5', 'k0']
    r = m.idempotency_keys(six[:5] + [('k0', 0)])
    assert r['statuses'] == ['executed'] * 5 + ['replayed'] and r['remembered'] == ['k0', 'k1', 'k2', 'k3', 'k4']
    # a replay does not refresh: after k0 replays, k0 is still the oldest and is evicted first
    r = m.idempotency_keys(six[:5] + [('k0', 0), ('k5', 5), ('k0', 0)])
    assert r['statuses'] == ['executed'] * 5 + ['replayed', 'executed', 'executed'] and r['remembered'] == ['k2', 'k3', 'k4', 'k5', 'k0']
    assert m.idempotency_keys([('a', 1), ('b', 1), ('a', 1)], 1)['statuses'] == ['executed', 'executed', 'executed']
    assert m.idempotency_keys([('a', 1), ('b', 1), ('b', 1)], 1)['statuses'] == ['executed', 'executed', 'replayed']
    assert m.idempotency_keys([('a', 1), ('b', 1), ('a', 1)], 2)['statuses'] == ['executed', 'executed', 'replayed']
    assert m.idempotency_keys([('a', 1)] * 40, 20)['counts'] == {'executed': 1, 'replayed': 39, 'conflict': 0}
    assert m.idempotency_keys([('k%d' % i, i) for i in range(20)], 20)['remembered'] == ['k%d' % i for i in range(20)]
    assert m.idempotency_keys([('k%d' % i, i) for i in range(21)], 20)['remembered'] == ['k%d' % i for i in range(1, 21)]
    assert m.idempotency_keys([['a', 1000], ('a', 1000), ('b', 0)])['counts']['replayed'] == 1
    assert m.idempotency_keys((('z' * 12, 7),))['remembered'] == ['z' * 12]
    # a conflicting request is not stored: the first payload stays
    assert m.idempotency_keys([('a', 1), ('a', 2), ('a', 1)])['statuses'] == ['executed', 'conflict', 'replayed']
    rng = random.Random(652)
    for _ in range(600):
        cap = rng.randint(1, 20)
        reqs = [(rng.choice('abcdefghijklmnopqrstuvwx'), rng.choice([0, 1, 2])) for _ in range(rng.randint(0, 40))]
        assert m.idempotency_keys(reqs, cap) == _oracle(reqs, cap), (reqs, cap)
        assert m.idempotency_keys(reqs) == _oracle(reqs, 5)


def _late(m):
    RQ = 'requests must be a list or tuple'
    SZ = 'requests must contain at most 40 entries'
    CP = 'capacity must be a nonbool integer between 1 and 20'
    PR = 'each request must be a (key, payload) pair'
    KY = 'keys must be strings of 1 to 12 characters'
    PL = 'payload must be a nonbool integer between 0 and 1000'
    ok = ('a', 1)
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, RQ, m.idempotency_keys, bad)
    _raises(TypeError, RQ, m.idempotency_keys, L([ok] * 41))
    _raises(ValueError, SZ, m.idempotency_keys, [ok] * 41)
    assert m.idempotency_keys([ok] * 40)['counts']['replayed'] == 39
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, CP, m.idempotency_keys, [ok], bad)
    assert m.idempotency_keys([ok], 1) and m.idempotency_keys([ok], 20)
    for K in (L, T):
        for bad in (K(ok), K(('a',))):
            _raises(ValueError, PR, m.idempotency_keys, [bad])
            _raises(ValueError, PR, m.idempotency_keys, [ok, bad])
    for bad in ('ab', None, 5, ('a',), ('a', 1, 1), ()):
        _raises(ValueError, PR, m.idempotency_keys, [bad])
        _raises(ValueError, PR, m.idempotency_keys, [ok, bad])
    for bad in ('', 'x' * 13, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, KY, m.idempotency_keys, [(bad, 1)])
        _raises(ValueError, KY, m.idempotency_keys, [ok, (bad, 1)])
    for bad in (-1, 1001, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, PL, m.idempotency_keys, [('b', bad)])
        _raises(ValueError, PL, m.idempotency_keys, [ok, ('b', bad)])
    assert m.idempotency_keys([('a', 0), ('b', 1000)])['counts']['executed'] == 2
    # order: type, size, capacity, then per request: shape, key, payload
    _raises(TypeError, RQ, m.idempotency_keys, L([1]), I(1))
    _raises(ValueError, SZ, m.idempotency_keys, [1] * 41, I(1))
    _raises(ValueError, CP, m.idempotency_keys, [1], I(1))
    _raises(ValueError, PR, m.idempotency_keys, [1], 5)
    _raises(ValueError, KY, m.idempotency_keys, [(5, I(1))])
    _raises(ValueError, PL, m.idempotency_keys, [('b', I(1)), (5, 1)])


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
    def __hash__(self): return hash('b')


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
    ("type(requests) not in (list, tuple)", "not isinstance(requests, (list, tuple))"),
    ("len(requests) > MAX_REQUESTS", "len(requests) >= MAX_REQUESTS"),
    ("MAX_REQUESTS = 40", "MAX_REQUESTS = 41"),
    ("capacity=5", "capacity=4"),
    ("capacity=5", "capacity=6"),
    ("type(capacity) is not int or not 1 <= capacity <= 20", "not isinstance(capacity, int) or not 1 <= capacity <= 20"),
    ("type(capacity) is not int or not 1 <= capacity <= 20", "isinstance(capacity, bool) or not isinstance(capacity, int) or not 1 <= capacity <= 20"),
    ("not 1 <= capacity <= 20", "not 0 <= capacity <= 20"),
    ("not 1 <= capacity <= 20", "not 1 <= capacity < 20"),
    ("not 1 <= capacity <= 20", "not 1 <= capacity <= 21"),
    ("type(r) not in (list, tuple) or len(r) != 2", "not isinstance(r, (list, tuple)) or len(r) != 2"),
    ("or len(r) != 2", "or len(r) > 2"),
    ("or len(r) != 2", "or len(r) < 2"),
    ("type(key) is not str or not 1 <= len(key) <= 12", "not isinstance(key, str) or not 1 <= len(key) <= 12"),
    ("not 1 <= len(key) <= 12", "not 0 <= len(key) <= 12"),
    ("not 1 <= len(key) <= 12", "not 1 <= len(key) < 12"),
    ("not 1 <= len(key) <= 12", "not 1 <= len(key) <= 13"),
    ("type(payload) is not int or not 0 <= payload <= 1000", "not isinstance(payload, int) or not 0 <= payload <= 1000"),
    ("type(payload) is not int or not 0 <= payload <= 1000", "isinstance(payload, bool) or not isinstance(payload, int) or not 0 <= payload <= 1000"),
    ("not 0 <= payload <= 1000", "not 0 < payload <= 1000"),
    ("not 0 <= payload <= 1000", "not 0 <= payload < 1000"),
    ("not 0 <= payload <= 1000", "not 0 <= payload <= 1001"),
    ("'replayed' if store[key] == payload else 'conflict'", "'conflict' if store[key] == payload else 'replayed'"),
    ("'replayed' if store[key] == payload else 'conflict'", "'replayed'"),
    ("statuses.append('replayed' if store[key] == payload else 'conflict')", "statuses.append('replayed' if store[key] == payload else 'conflict'); store[key] = store.pop(key)"),
    ("if len(store) > capacity:", "if len(store) >= capacity:"),
    ("del store[next(iter(store))]", "del store[list(store)[-1]]"),
    ("for s in ('executed', 'replayed', 'conflict')}", "for s in ('executed', 'replayed')}"),
    ("'remembered': list(store)", "'remembered': sorted(store)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
