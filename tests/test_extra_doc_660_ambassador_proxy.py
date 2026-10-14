import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ambassador_proxy as mod

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
    assert mod.SCOPE == 'PARTIAL: allow-list and rate decisions over supplied requests, no real proxying'
    assert len(mod.NOT_CLAIMED) >= 4 and 'authentication' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(allowed, reqs, lim):
    """Independent: count earlier forwards of the same client by scanning."""
    st = []
    for i, (c, p) in enumerate(reqs):
        if p not in list(allowed):
            st.append('denied')
        elif sum(1 for j in range(i) if st[j] == 'forwarded' and reqs[j][0] == c) >= lim:
            st.append('rate_limited')
        else:
            st.append('forwarded')
    fw = {}
    for i, (c, _) in enumerate(reqs):
        if st[i] == 'forwarded':
            fw[c] = fw.get(c, 0) + 1
    return {'statuses': st, 'forwarded': fw, 'counts': {k: st.count(k) for k in ('forwarded', 'denied', 'rate_limited')}}


def _core(m):
    A = ['/a', '/b']
    assert m.ambassador_proxy(A, []) == {'statuses': [], 'forwarded': {}, 'counts': {'forwarded': 0, 'denied': 0, 'rate_limited': 0}}
    r = m.ambassador_proxy(A, [('u', '/a'), ('u', '/x'), ('v', '/b'), ('u', '/b')])
    assert r == {'statuses': ['forwarded', 'denied', 'forwarded', 'forwarded'], 'forwarded': {'u': 2, 'v': 1}, 'counts': {'forwarded': 3, 'denied': 1, 'rate_limited': 0}}
    assert list(r['counts']) == ['forwarded', 'denied', 'rate_limited']
    # default 3 per client: the fourth is limited, a different client is not, denied requests do not count
    reqs = [('u', '/a')] * 4 + [('v', '/a')]
    r = m.ambassador_proxy(A, reqs)
    assert r['statuses'] == ['forwarded'] * 3 + ['rate_limited', 'forwarded'] and r['forwarded'] == {'u': 3, 'v': 1}
    assert m.ambassador_proxy(A, reqs[:3])['counts']['rate_limited'] == 0
    assert m.ambassador_proxy(A, reqs, 4)['statuses'] == ['forwarded'] * 5
    assert m.ambassador_proxy(A, reqs, 1)['statuses'] == ['forwarded', 'rate_limited', 'rate_limited', 'rate_limited', 'forwarded']
    r = m.ambassador_proxy(A, [('u', '/x')] * 5 + [('u', '/a')] * 3 + [('u', '/x'), ('u', '/a')])
    assert r['statuses'] == ['denied'] * 5 + ['forwarded'] * 3 + ['denied', 'rate_limited']
    assert m.ambassador_proxy(A, [('u', '/a')] * 3 + [('u', '/x')])['statuses'][-1] == 'denied'    # denied wins over limited
    assert m.ambassador_proxy(['/a'], [['u', '/a'], ('u', '/A')])['statuses'] == ['forwarded', 'denied']
    assert m.ambassador_proxy(('/a',), (('u', '/a'),))['forwarded'] == {'u': 1}
    assert m.ambassador_proxy(['p%d' % i for i in range(6)], [('c', 'p5')] * 40, 20)['forwarded'] == {'c': 20}
    assert m.ambassador_proxy(['/' * 16], [('c' * 12, '/' * 16)])['forwarded'] == {'c' * 12: 1}
    assert list(m.ambassador_proxy(A, [('z', '/a'), ('a', '/a'), ('z', '/a')])['forwarded']) == ['z', 'a']
    rng = random.Random(660)
    for _ in range(500):
        allowed = rng.sample(['/a', '/b', '/c', '/d'], rng.randint(1, 4))
        reqs = [(rng.choice('uvw'), rng.choice(['/a', '/b', '/c', '/d', '/z'])) for _ in range(rng.randint(0, 40))]
        lim = rng.choice([1, 2, 3, 5, 20])
        assert m.ambassador_proxy(allowed, reqs, lim) == _oracle(allowed, reqs, lim), (allowed, reqs, lim)
        assert m.ambassador_proxy(allowed, reqs) == _oracle(allowed, reqs, 3)


def _late(m):
    AT = 'allowed_paths must be a list or tuple'
    AS = 'allowed_paths must contain 1 to 6 entries'
    RT = 'requests must be a list or tuple'
    RS = 'requests must contain at most 40 entries'
    RL = 'rate_limit must be a nonbool integer between 1 and 20'
    PA = 'paths must be strings of 1 to 16 characters'
    DP = 'duplicate allowed path'
    PR = 'each request must be a (client, path) pair'
    CL = 'clients must be strings of 1 to 12 characters'
    ok = ('u', '/a')
    for bad in ('ab', None, 5, {}, L(['/a']), T(['/a']), L(), T()):
        _raises(TypeError, AT, m.ambassador_proxy, bad, [])
    _raises(TypeError, AT, m.ambassador_proxy, L(['/a'] * 7), [])
    _raises(ValueError, AS, m.ambassador_proxy, [], [])
    _raises(ValueError, AS, m.ambassador_proxy, ['/a'] * 7, [])
    assert m.ambassador_proxy(['p%d' % i for i in range(6)], [])['statuses'] == []
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, RT, m.ambassador_proxy, ['/a'], bad)
    _raises(TypeError, RT, m.ambassador_proxy, ['/a'], L([ok] * 41))
    _raises(ValueError, RS, m.ambassador_proxy, ['/a'], [ok] * 41)
    assert m.ambassador_proxy(['/a'], [ok] * 40, 20)['counts']['forwarded'] == 20
    for bad in (0, 21, -1, True, False, 1.0, '1', None, I(3), LyingI(3), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, RL, m.ambassador_proxy, ['/a'], [], bad)
    assert m.ambassador_proxy(['/a'], [ok], 1) and m.ambassador_proxy(['/a'], [ok], 20)
    for bad in ('', 'x' * 17, None, 5, S('/a'), LyingS('/a'), b'/a', ['/a']):
        _raises(ValueError, PA, m.ambassador_proxy, [bad], [])
        _raises(ValueError, PA, m.ambassador_proxy, ['/a', bad], [])
    _raises(ValueError, DP, m.ambassador_proxy, ['/a', '/a'], [])
    _raises(ValueError, DP, m.ambassador_proxy, ['/a', '/b', '/a'], [])
    for K in (L, T):
        for bad in (K(ok), K(('u',))):
            _raises(ValueError, PR, m.ambassador_proxy, ['/a'], [bad])
            _raises(ValueError, PR, m.ambassador_proxy, ['/a'], [ok, bad])
    for bad in ('ab', None, 5, ('u',), ('u', '/a', 1), ()):
        _raises(ValueError, PR, m.ambassador_proxy, ['/a'], [bad])
        _raises(ValueError, PR, m.ambassador_proxy, ['/a'], [ok, bad])
    for bad in ('', 'x' * 13, None, 5, S('u'), LyingS('u'), b'u'):
        _raises(ValueError, CL, m.ambassador_proxy, ['/a'], [(bad, '/a')])
        _raises(ValueError, CL, m.ambassador_proxy, ['/a'], [ok, (bad, '/a')])
    for bad in ('', 'x' * 17, None, 5, S('/a'), LyingS('/a'), b'/a'):
        _raises(ValueError, PA, m.ambassador_proxy, ['/a'], [('u', bad)])
        _raises(ValueError, PA, m.ambassador_proxy, ['/a'], [ok, ('u', bad)])
    # order: allowed type, size, requests type, size, rate_limit, allowed entries, request rows
    _raises(TypeError, AT, m.ambassador_proxy, L(), L([1]), I(1))
    _raises(ValueError, AS, m.ambassador_proxy, [], L([1]), I(1))
    _raises(TypeError, RT, m.ambassador_proxy, [5], L([1]), I(1))
    _raises(ValueError, RS, m.ambassador_proxy, [5], [1] * 41, I(1))
    _raises(ValueError, RL, m.ambassador_proxy, [5], [1], I(1))
    _raises(ValueError, PA, m.ambassador_proxy, [5, 5], [1], 3)
    _raises(ValueError, DP, m.ambassador_proxy, ['/a', '/a'], [1], 3)
    _raises(ValueError, PR, m.ambassador_proxy, ['/a'], [1])
    _raises(ValueError, CL, m.ambassador_proxy, [ '/a'], [(5, 5)])


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
    def __hash__(self): return hash('/a')


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
    ("type(allowed_paths) not in (list, tuple)", "not isinstance(allowed_paths, (list, tuple))"),
    ("not 1 <= len(allowed_paths) <= 6", "not 0 <= len(allowed_paths) <= 6"),
    ("not 1 <= len(allowed_paths) <= 6", "not 1 <= len(allowed_paths) < 6"),
    ("not 1 <= len(allowed_paths) <= 6", "not 1 <= len(allowed_paths) <= 7"),
    ("type(requests) not in (list, tuple)", "not isinstance(requests, (list, tuple))"),
    ("len(requests) > 40", "len(requests) >= 40"),
    ("len(requests) > 40", "len(requests) > 41"),
    ("rate_limit=3", "rate_limit=2"),
    ("rate_limit=3", "rate_limit=4"),
    ("type(rate_limit) is not int or not 1 <= rate_limit <= 20", "not isinstance(rate_limit, int) or not 1 <= rate_limit <= 20"),
    ("type(rate_limit) is not int or not 1 <= rate_limit <= 20", "isinstance(rate_limit, bool) or not isinstance(rate_limit, int) or not 1 <= rate_limit <= 20"),
    ("not 1 <= rate_limit <= 20", "not 0 <= rate_limit <= 20"),
    ("not 1 <= rate_limit <= 20", "not 1 <= rate_limit < 20"),
    ("not 1 <= rate_limit <= 20", "not 1 <= rate_limit <= 21"),
    ("type(p) is not str or not 1 <= len(p) <= 16", "not isinstance(p, str) or not 1 <= len(p) <= 16"),
    ("not 1 <= len(p) <= 16", "not 0 <= len(p) <= 16"),
    ("not 1 <= len(p) <= 16", "not 1 <= len(p) < 16"),
    ("not 1 <= len(p) <= 16", "not 1 <= len(p) <= 17"),
    ("if p in allowed:", "if False:"),
    ("type(r) not in (list, tuple) or len(r) != 2", "not isinstance(r, (list, tuple)) or len(r) != 2"),
    ("or len(r) != 2", "or len(r) > 2"),
    ("or len(r) != 2", "or len(r) < 2"),
    ("type(client) is not str or not 1 <= len(client) <= 12", "not isinstance(client, str) or not 1 <= len(client) <= 12"),
    ("not 1 <= len(client) <= 12", "not 0 <= len(client) <= 12"),
    ("not 1 <= len(client) <= 12", "not 1 <= len(client) < 12"),
    ("not 1 <= len(client) <= 12", "not 1 <= len(client) <= 13"),
    ("type(path) is not str or not 1 <= len(path) <= 16", "not isinstance(path, str) or not 1 <= len(path) <= 16"),
    ("not 1 <= len(path) <= 16", "not 0 <= len(path) <= 16"),
    ("not 1 <= len(path) <= 16", "not 1 <= len(path) < 16"),
    ("not 1 <= len(path) <= 16", "not 1 <= len(path) <= 17"),
    ("if path not in allowed:", "if path in allowed:"),
    ("elif forwarded.get(client, 0) >= rate_limit:", "elif forwarded.get(client, 0) > rate_limit:"),
    ("elif forwarded.get(client, 0) >= rate_limit:", "elif sum(forwarded.values()) >= rate_limit:"),
    ("forwarded[client] = forwarded.get(client, 0) + 1", "forwarded[client] = forwarded.get(client, 0) + 2"),
    ("for s in ('forwarded', 'denied', 'rate_limited')}", "for s in ('forwarded', 'denied')}"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
