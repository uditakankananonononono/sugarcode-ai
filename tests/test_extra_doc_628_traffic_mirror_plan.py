import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import traffic_mirror_plan as mod

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
    assert mod.SCOPE == 'PARTIAL: even selection of supplied safe requests for mirroring, no real copying'
    assert len(mod.NOT_CLAIMED) >= 4 and 'copying real traffic' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(requests, pct):
    """Independent: the mirrored count after k eligible requests must be floor(k * pct / 100)."""
    from fractions import Fraction
    import math
    elig = [r for r in requests if r[1] in ('GET', 'HEAD')]
    target = [math.floor(Fraction(k * pct, 100)) for k in range(len(elig) + 1)]
    picked = {elig[k][0] for k in range(len(elig)) if target[k + 1] - target[k] == 1}
    assert all(target[k + 1] - target[k] in (0, 1) for k in range(len(elig)))
    mir = [r[0] for r in requests if r[0] in picked]
    return {'mirrored': mir, 'skipped': [r[0] for r in requests if r[1] not in ('GET', 'HEAD')],
            'eligible': len(elig), 'count': len(mir)}


def _core(m):
    reqs = [('r%d' % i, 'GET') for i in range(8)]
    assert m.mirror_plan(reqs, 25) == {'mirrored': ['r3', 'r7'], 'skipped': [], 'eligible': 8, 'count': 2}
    assert m.mirror_plan(reqs) == m.mirror_plan(reqs, 25)
    assert m.mirror_plan(reqs, 50)['mirrored'] == ['r1', 'r3', 'r5', 'r7']
    assert m.mirror_plan(reqs, 100)['mirrored'] == ['r%d' % i for i in range(8)]
    assert m.mirror_plan(reqs, 0) == {'mirrored': [], 'skipped': [], 'eligible': 8, 'count': 0}
    assert m.mirror_plan(reqs, 99)['count'] == 7 and m.mirror_plan(reqs, 1)['count'] == 0
    assert m.mirror_plan(reqs, 13)['mirrored'] == ['r7'] and m.mirror_plan(reqs, 12)['mirrored'] == []
    assert m.mirror_plan(reqs, 34)['mirrored'] == ['r2', 'r5']
    mixed = [('a', 'GET'), ('b', 'POST'), ('c', 'HEAD'), ('d', 'PUT'), ('e', 'DELETE'), ('f', 'GET'), ('g', 'HEAD')]
    assert m.mirror_plan(mixed, 50) == {'mirrored': ['c', 'g'], 'skipped': ['b', 'd', 'e'], 'eligible': 4, 'count': 2}
    assert m.mirror_plan(tuple(mixed), 100)['mirrored'] == ['a', 'c', 'f', 'g']
    assert m.mirror_plan([['p', 'POST'], ('q', 'GET')], 100) == {'mirrored': ['q'], 'skipped': ['p'], 'eligible': 1, 'count': 1}
    assert m.mirror_plan([('p', 'POST')], 100) == {'mirrored': [], 'skipped': ['p'], 'eligible': 0, 'count': 0}
    assert m.mirror_plan([]) == {'mirrored': [], 'skipped': [], 'eligible': 0, 'count': 0}
    assert m.mirror_plan([('x' * 16, 'HEAD')], 100)['mirrored'] == ['x' * 16]
    hundred = [('n%d' % i, 'GET') for i in range(100)]
    assert m.mirror_plan(hundred, 25)['count'] == 25 and m.mirror_plan(hundred, 100)['count'] == 100
    assert m.mirror_plan(hundred, 33)['count'] == 33
    assert m.mirror_plan(hundred) == m.mirror_plan(hundred, 25) and m.mirror_plan(hundred)['mirrored'][:2] == ['n3', 'n7']
    assert m.mirror_plan(hundred, 26)['count'] == 26 and m.mirror_plan(hundred, 24)['count'] == 24
    # unsorted ids keep arrival order
    assert m.mirror_plan([('z', 'GET'), ('a', 'GET')], 100)['mirrored'] == ['z', 'a']
    assert m.mirror_plan([('z', 'POST'), ('a', 'PUT')], 100)['skipped'] == ['z', 'a']
    rng = random.Random(628)
    for _ in range(500):
        reqs = [('i%d' % k, rng.choice(('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'GET'))) for k in range(rng.randint(0, 30))]
        pct = rng.choice((0, 1, 25, 33, 50, 99, 100, rng.randint(0, 100)))
        assert m.mirror_plan(reqs, pct) == _oracle(reqs, pct), (reqs, pct)


def _late(m):
    RQ = 'requests must be a list or tuple'
    PC = 'percent must be a nonbool integer between 0 and 100'
    PR = 'each request must be a (request_id, method) pair'
    RI = 'request ids must be strings of 1 to 16 characters'
    MT = 'method must be one of GET, HEAD, POST, PUT, DELETE'
    good = ('a', 'GET')
    for bad in ('ab', None, 5, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, RQ, m.mirror_plan, bad)
    _raises(TypeError, RQ, m.mirror_plan, L([good] * 101))
    _raises(ValueError, 'requests must contain at most 100 entries', m.mirror_plan, [('i%d' % k, 'GET') for k in range(101)])
    for bad in (-1, 101, True, False, 1.0, '1', None, I(25), LyingI(25), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, PC, m.mirror_plan, [good], bad)
    for K in (L, T):
        for bad in (K(good), K(('a',))):
            _raises(ValueError, PR, m.mirror_plan, [bad])
            _raises(ValueError, PR, m.mirror_plan, [good, bad])
    for bad in ('ab', None, 5, ('a',), ('a', 'GET', 1), ()):
        _raises(ValueError, PR, m.mirror_plan, [bad])
        _raises(ValueError, PR, m.mirror_plan, [good, bad])
    for bad in ('', 'x' * 17, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, RI, m.mirror_plan, [(bad, 'GET')])
        _raises(ValueError, RI, m.mirror_plan, [good, (bad, 'GET')])
    for bad in ('get', 'OPTIONS', 'PATCH', '', None, 5, S('GET'), LyingS('GET'), LyingS('zzz'), ['GET'], b'GET'):
        _raises(ValueError, MT, m.mirror_plan, [('b', bad)])
        _raises(ValueError, MT, m.mirror_plan, [good, ('b', bad)])
    for ok in ('GET', 'HEAD', 'POST', 'PUT', 'DELETE'):
        assert m.mirror_plan([('b', ok)])['eligible'] == (1 if ok in ('GET', 'HEAD') else 0)
    _raises(ValueError, 'duplicate request id', m.mirror_plan, [good, good])
    _raises(ValueError, 'duplicate request id', m.mirror_plan, [good, ('b', 'POST'), good])
    _raises(ValueError, 'duplicate request id', m.mirror_plan, [('a', 'POST'), ('a', 'GET')])
    # order: requests, size, percent, then per request: shape, id, method, duplicate
    _raises(TypeError, RQ, m.mirror_plan, L([1]), I(1))
    _raises(ValueError, PC, m.mirror_plan, [1], I(1))
    _raises(ValueError, PR, m.mirror_plan, [1], 5)
    _raises(ValueError, RI, m.mirror_plan, [(S('a'), S('GET'))])
    _raises(ValueError, MT, m.mirror_plan, [('a', S('GET')), ('a', 'GET')])      # method before the duplicate check


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
    def __hash__(self): return hash('GET')


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


def test_result_is_fresh_and_requests_unchanged():
    reqs = [('a', 'GET')]
    r = mod.mirror_plan(reqs, 100)
    r['mirrored'].append('zzz')
    assert reqs == [('a', 'GET')]
    assert mod.mirror_plan(reqs, 100)['mirrored'] == ['a']


MUTANTS = [
    ("type(requests) not in (list, tuple)", "not isinstance(requests, (list, tuple))"),
    ("len(requests) > MAX_REQUESTS", "len(requests) >= MAX_REQUESTS"),
    ("MAX_REQUESTS = 100", "MAX_REQUESTS = 101"),
    ("METHODS = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE')", "METHODS = ('GET', 'HEAD', 'POST', 'PUT')"),
    ("METHODS = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE')", "METHODS = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH')"),
    ("SAFE = ('GET', 'HEAD')", "SAFE = ('GET',)"),
    ("SAFE = ('GET', 'HEAD')", "SAFE = ('GET', 'HEAD', 'POST')"),
    ("type(percent) is not int or not 0 <= percent <= 100", "isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100"),
    ("type(percent) is not int or not 0 <= percent <= 100", "not isinstance(percent, int) or not 0 <= percent <= 100"),
    ("not 0 <= percent <= 100", "not 1 <= percent <= 100"),
    ("not 0 <= percent <= 100", "not 0 <= percent < 100"),
    ("not 0 <= percent <= 100", "not 0 <= percent <= 101"),
    ("percent=25", "percent=26"),
    ("percent=25", "percent=24"),
    ("type(r) not in (list, tuple) or len(r) != 2", "not isinstance(r, (list, tuple)) or len(r) != 2"),
    ("or len(r) != 2", "or len(r) > 2"),
    ("or len(r) != 2", "or len(r) < 2"),
    ("type(rid) is not str", "not isinstance(rid, str)"),
    ("not 1 <= len(rid) <= 16", "not 0 <= len(rid) <= 16"),
    ("not 1 <= len(rid) <= 16", "not 1 <= len(rid) <= 17"),
    ("not 1 <= len(rid) <= 16", "not 1 <= len(rid) < 16"),
    ("type(method) is not str or method not in METHODS", "method not in METHODS"),
    ("type(method) is not str or method not in METHODS", "not isinstance(method, str) or method not in METHODS"),
    ("if rid in seen:", "if False:"),
    ("if method not in SAFE:", "if method == 'POST':"),
    ("if method not in SAFE:", "if False:"),
    ("(k + 1) * percent // 100 > k * percent // 100", "(k + 1) * percent // 100 >= k * percent // 100"),
    ("(k + 1) * percent // 100 > k * percent // 100", "(k + 1) * percent // 100 > (k - 1) * percent // 100"),
    ("(k + 1) * percent // 100 > k * percent // 100", "k * percent // 100 > (k - 1) * percent // 100"),
    ("(k + 1) * percent // 100 > k * percent // 100", "(k + 1) * percent // 99 > k * percent // 99"),
    ("(k + 1) * percent // 100 > k * percent // 100", "-(-(k + 1) * percent // 100) > -(-k * percent // 100)"),
    ("        k += 1\n", "        k += 2\n"),
    ("'eligible': k", "'eligible': len(requests)"),
    ("'count': len(mirrored)", "'count': len(skipped)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
