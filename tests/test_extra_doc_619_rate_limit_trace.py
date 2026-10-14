import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import rate_limit_trace as mod

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
    assert mod.SCOPE == 'PARTIAL: token-bucket replay of supplied request times, no real clock or clients'
    assert len(mod.NOT_CLAIMED) >= 4 and 'real clocks' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(times, cap, interval):
    """Independent: advance one time unit at a time with a phase counter."""
    tokens, phase, res, i, u = cap, 0, [], 0, 0
    while i < len(times):
        if u > 0:
            phase += 1
            if tokens < cap and phase == interval:
                tokens, phase = tokens + 1, 0
            if tokens == cap:
                phase = 0
        while i < len(times) and times[i] == u:
            if tokens >= 1:
                tokens -= 1
                res.append('allowed')
            else:
                res.append('limited')
            i += 1
        u += 1
    a = res.count('allowed')
    return {'results': res, 'allowed': a, 'limited': len(res) - a, 'tokens': tokens}


def _core(m):
    r = m.rate_limit_trace([0] * 6 + [9, 10, 10, 19, 20], 5, 10)
    assert r['results'] == ['allowed'] * 5 + ['limited', 'limited', 'allowed', 'limited', 'limited', 'allowed']
    assert (r['allowed'], r['limited'], r['tokens']) == (7, 4, 0)
    assert m.rate_limit_trace([]) == {'results': [], 'allowed': 0, 'limited': 0, 'tokens': 5}
    assert m.rate_limit_trace([7], 1, 1) == {'results': ['allowed'], 'allowed': 1, 'limited': 0, 'tokens': 0}
    assert m.rate_limit_trace([0, 0], 1, 1000) == {'results': ['allowed', 'limited'], 'allowed': 1, 'limited': 1, 'tokens': 0}
    # interval edges: one unit early is limited, exactly on the interval is allowed
    assert m.rate_limit_trace([0, 0, 9, 10], 2, 10)['results'] == ['allowed', 'allowed', 'limited', 'allowed']
    assert m.rate_limit_trace([0, 1, 999, 1000], 1, 1000)['results'] == ['allowed', 'limited', 'limited', 'allowed']
    # several tokens come back at once, capped at the capacity
    assert m.rate_limit_trace([0, 0, 0, 30, 30, 30, 30], 3, 10)['results'] == ['allowed'] * 6 + ['limited']
    assert m.rate_limit_trace([0, 0, 0, 20, 20, 20], 3, 10)['results'] == ['allowed'] * 3 + ['allowed', 'allowed', 'limited']
    assert m.rate_limit_trace([0, 1000000], 100, 1)['tokens'] == 99
    # a full bucket earns nothing toward the next token while it is full
    assert m.rate_limit_trace([5, 10, 14, 15], 1, 10)['results'] == ['allowed', 'limited', 'limited', 'allowed']
    assert m.rate_limit_trace([5, 15, 16, 25], 1, 10)['results'] == ['allowed', 'allowed', 'limited', 'allowed']
    # partial progress is kept while the bucket is not full
    assert m.rate_limit_trace([0, 0, 15, 15, 20, 20], 2, 10)['results'] == ['allowed', 'allowed', 'allowed', 'limited', 'allowed', 'limited']
    # defaults: capacity 5, interval 10, with several requests on each side
    d = [0] * 7 + [10, 10, 19, 20]
    assert m.rate_limit_trace(d)['results'] == ['allowed'] * 5 + ['limited'] * 2 + ['allowed', 'limited', 'limited', 'allowed']
    assert m.rate_limit_trace(d, 5, 10) == m.rate_limit_trace(d)
    assert m.rate_limit_trace((0, 0, 0))['allowed'] == 3
    rng = random.Random(619)
    for _ in range(600):
        n = rng.randint(0, 25)
        t, ts = 0, []
        for _ in range(n):
            t += rng.choice((0, 0, 1, 2, 5, 9, 10, 11, 25))
            ts.append(t)
        cap, interval = rng.randint(1, 6), rng.randint(1, 12)
        assert m.rate_limit_trace(ts, cap, interval) == _oracle(ts, cap, interval), (ts, cap, interval)


def _late(m):
    RQ = 'requests must be a list or tuple'
    CP = 'capacity must be a nonbool integer between 1 and 100'
    IV = 'interval must be a nonbool integer between 1 and 1000'
    TM = 'times must be nonbool integers between 0 and 1000000'
    for bad in ('ab', None, 5, {}, L([0]), T([0]), L(), T()):
        _raises(TypeError, RQ, m.rate_limit_trace, bad)
    _raises(TypeError, RQ, m.rate_limit_trace, L([0] * 101))
    _raises(ValueError, 'requests must contain at most 100 entries', m.rate_limit_trace, [0] * 101)
    assert m.rate_limit_trace([0] * 100, 100, 1)['allowed'] == 100
    assert m.rate_limit_trace([0] * 100, 1, 1)['limited'] == 99
    for bad in (0, 101, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, CP, m.rate_limit_trace, [0], bad)
    for bad in (0, 1001, True, False, 1.0, '1', None, I(10), LyingI(10), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, IV, m.rate_limit_trace, [0], 5, bad)
    assert m.rate_limit_trace([0], 100, 1000)['allowed'] == 1
    for bad in (-1, 1000001, True, False, 1.0, '1', None, (0,), [0], I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TM, m.rate_limit_trace, [bad])
        _raises(ValueError, TM, m.rate_limit_trace, [0, bad])
        _raises(ValueError, TM, m.rate_limit_trace, [0, 1, bad])
    _raises(ValueError, 'times must not decrease', m.rate_limit_trace, [5, 4])
    _raises(ValueError, 'times must not decrease', m.rate_limit_trace, [0, 5, 4])
    assert m.rate_limit_trace([5, 5], 5, 10)['allowed'] == 2
    _raises(TypeError, RQ, m.rate_limit_trace, L([I(1)]), I(1), I(1))
    _raises(ValueError, CP, m.rate_limit_trace, [I(1)], I(1), I(1))
    _raises(ValueError, IV, m.rate_limit_trace, [I(1)], 1, I(1))
    _raises(ValueError, TM, m.rate_limit_trace, [5, I(4)], 1, 1)               # type before order
    _raises(ValueError, 'times must not decrease', m.rate_limit_trace, [5, 4, I(3)], 1, 1)


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


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
    req = [0, 0]
    r = mod.rate_limit_trace(req, 1, 5)
    r['results'].append('x')
    assert req == [0, 0]
    assert mod.rate_limit_trace(req, 1, 5)['results'] == ['allowed', 'limited']


MUTANTS = [
    ("type(requests) not in (list, tuple)", "not isinstance(requests, (list, tuple))"),
    ("len(requests) > MAX_REQUESTS", "len(requests) >= MAX_REQUESTS"),
    ("MAX_REQUESTS = 100", "MAX_REQUESTS = 101"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(capacity, 1, 100", "_int(capacity, 0, 100"),
    ("_int(capacity, 1, 100", "_int(capacity, 1, 101"),
    ("_int(interval, 1, 1000", "_int(interval, 0, 1000"),
    ("_int(interval, 1, 1000", "_int(interval, 1, 1001"),
    ("_int(t, 0, MAX_TIME", "_int(t, 1, MAX_TIME"),
    ("MAX_TIME = 1000000", "MAX_TIME = 1000001"),
    ("if t < last:", "if t <= last:"),
    ("if t < last:", "if False:"),
    ("last = t\n    tokens", "last = 0\n    tokens"),
    ("capacity=5", "capacity=4"),
    ("capacity=5", "capacity=6"),
    ("interval=10", "interval=11"),
    ("interval=10", "interval=9"),
    ("gained = (t - clock) // interval", "gained = (t - clock) // interval + 1"),
    ("gained = (t - clock) // interval", "gained = (t - clock) // (interval + 1)"),
    ("gained = (t - clock) // interval", "gained = (t - clock + 1) // interval"),
    ("tokens + gained >= capacity", "tokens + gained > capacity"),
    ("tokens, clock = capacity, t", "tokens, clock = capacity, clock"),
    ("tokens, clock = tokens + gained, clock + gained * interval", "tokens, clock = tokens + gained, t"),
    ("tokens, clock = tokens + gained, clock + gained * interval", "tokens, clock = tokens + gained, clock + interval"),
    ("tokens, clock = tokens + gained, clock + gained * interval", "tokens, clock = tokens + 1, clock + gained * interval"),
    ("if tokens >= 1:", "if tokens > 1:"),
    ("tokens -= 1", "tokens -= 2"),
    ("tokens, clock, results = capacity, 0, []", "tokens, clock, results = capacity - 1, 0, []"),
    ("'limited': len(results) - allowed", "'limited': len(results)"),
    ("'tokens': tokens", "'tokens': tokens + 1"),
    ("results.append('limited')", "results.append('allowed')"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
