import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import circuit_breaker_trace as mod

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
    assert mod.SCOPE == 'PARTIAL: replay of a supplied call trace through a closed, open and half-open breaker, no real calls'
    assert len(mod.NOT_CLAIMED) >= 4 and 'real calls' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(events, thr, cd):
    """Independent: keeps the executed outcomes and recounts the trailing failures after each open."""
    executed, boundary, open_t, opens, res = [], 0, None, 0, []
    for t, ok in events:
        if open_t is not None and t - open_t < cd:
            res.append('rejected')
            continue
        was_open = open_t is not None
        executed.append(ok)
        res.append('success' if ok else 'failure')
        if ok:
            open_t = None
            continue
        streak = 0
        for x in reversed(executed[boundary:]):
            if x:
                break
            streak += 1
        if was_open or streak >= thr:
            open_t, boundary, opens = t, len(executed), opens + 1
    return {'results': res, 'state': 'closed' if open_t is None else 'open', 'opens': opens}


def _core(m):
    F, OK = False, True
    r = m.replay_breaker([(0, F), (1, F), (2, F), (3, OK), (11, OK), (12, F)])
    assert r == {'results': ['failure', 'failure', 'failure', 'rejected', 'rejected', 'failure'], 'state': 'open', 'opens': 2}
    r = m.replay_breaker([(0, F)] * 3 + [(5, F), (12, F), (22, OK)], 3, 10)
    assert r == {'results': ['failure', 'failure', 'failure', 'rejected', 'failure', 'success'], 'state': 'closed', 'opens': 2}
    assert m.replay_breaker([]) == {'results': [], 'state': 'closed', 'opens': 0}
    assert m.replay_breaker([(5, OK)]) == {'results': ['success'], 'state': 'closed', 'opens': 0}
    # a success resets the failure count
    assert m.replay_breaker([(0, F), (1, F), (2, OK), (3, F), (4, F)])['state'] == 'closed'
    assert m.replay_breaker([(0, F), (1, F), (2, F)])['state'] == 'open'
    # threshold 1 opens on the first failure; threshold 10 needs ten
    assert m.replay_breaker([(0, F)], 1, 5) == {'results': ['failure'], 'state': 'open', 'opens': 1}
    assert m.replay_breaker([(i, F) for i in range(9)], 10)['state'] == 'closed'
    assert m.replay_breaker([(i, F) for i in range(10)], 10) == {'results': ['failure'] * 10, 'state': 'open', 'opens': 1}
    # cooldown edge: exactly cooldown later is the probe, one earlier is rejected
    assert m.replay_breaker([(0, F), (4, OK), (5, OK)], 1, 5)['results'] == ['failure', 'rejected', 'success']
    assert m.replay_breaker([(0, F), (1, OK)], 1, 1)['results'] == ['failure', 'success']
    assert m.replay_breaker([(0, F), (0, OK)], 1, 1)['results'] == ['failure', 'rejected']
    assert m.replay_breaker([(0, F), (1000, OK)], 1, 1000)['results'] == ['failure', 'success']
    assert m.replay_breaker([(0, F), (999, OK)], 1, 1000)['results'] == ['failure', 'rejected']
    # a failed probe reopens at the probe's time
    r = m.replay_breaker([(0, F), (5, F), (9, OK), (10, OK)], 1, 5)
    assert r == {'results': ['failure', 'failure', 'rejected', 'success'], 'state': 'closed', 'opens': 2}
    # rejected calls do not count, whatever their outcome
    assert m.replay_breaker([(0, F), (1, F), (2, F), (3, F)], 1, 10)['opens'] == 1
    # after a close the count starts again from zero
    r = m.replay_breaker([(0, F), (10, OK), (11, F), (12, F), (13, F)], 1, 10)
    assert r['results'] == ['failure', 'success', 'failure', 'rejected', 'rejected'] and r['opens'] == 2
    # defaults: threshold 3, cooldown 10, with several events on each side
    d = [(0, F), (1, F), (2, F), (11, OK), (12, OK), (13, OK)]
    assert m.replay_breaker(d)['results'] == ['failure', 'failure', 'failure', 'rejected', 'success', 'success']
    assert m.replay_breaker(d, 3, 10) == m.replay_breaker(d)
    assert m.replay_breaker([(0, F), (1, F)])['state'] == 'closed'
    assert m.replay_breaker(tuple([[0, F], (1, F), [2, F]]))['opens'] == 1
    assert m.replay_breaker([(1000000, F)])['results'] == ['failure']
    rng = random.Random(618)
    for _ in range(600):
        n = rng.randint(0, 25)
        t, ev = 0, []
        for _ in range(n):
            t += rng.randint(0, 6)
            ev.append((t, rng.random() < 0.4))
        thr, cd = rng.randint(1, 5), rng.randint(1, 12)
        assert m.replay_breaker(ev, thr, cd) == _oracle(ev, thr, cd), (ev, thr, cd)


def _late(m):
    EV = 'events must be a list or tuple'
    TH = 'threshold must be a nonbool integer between 1 and 10'
    CD = 'cooldown must be a nonbool integer between 1 and 1000'
    PR = 'each event must be a (time, ok) pair'
    TM = 'time must be a nonbool integer between 0 and 1000000'
    OKM = 'ok must be a bool'
    good = (0, True)
    for bad in ('ab', None, 5, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, EV, m.replay_breaker, bad)
    _raises(TypeError, EV, m.replay_breaker, L([good] * 101))
    _raises(ValueError, 'events must contain at most 100 entries', m.replay_breaker, [(0, True)] * 101)
    assert len(m.replay_breaker([(0, True)] * 100)['results']) == 100
    for bad in (0, 11, True, False, 1.0, '1', None, I(3), LyingI(3), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TH, m.replay_breaker, [good], bad)
    for bad in (0, 1001, True, False, 1.0, '1', None, I(10), LyingI(10), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, CD, m.replay_breaker, [good], 3, bad)
    for K in (L, T):
        for bad in (K(good), K((0,))):
            _raises(ValueError, PR, m.replay_breaker, [bad])
            _raises(ValueError, PR, m.replay_breaker, [good, bad])
    for bad in ('ab', None, 5, (0,), (0, True, 1), ()):
        _raises(ValueError, PR, m.replay_breaker, [bad])
        _raises(ValueError, PR, m.replay_breaker, [good, bad])
    for bad in (-1, 1000001, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TM, m.replay_breaker, [(bad, True)])
        _raises(ValueError, TM, m.replay_breaker, [good, (bad, True)])
    for bad in (1, 0, None, 'x', 1.0, I(1), LyingI(1), [True]):
        _raises(ValueError, OKM, m.replay_breaker, [(0, bad)])
        _raises(ValueError, OKM, m.replay_breaker, [good, (1, bad)])
    _raises(ValueError, 'times must not decrease', m.replay_breaker, [(5, True), (4, True)])
    _raises(ValueError, 'times must not decrease', m.replay_breaker, [(0, True), (5, True), (4, False)])
    assert m.replay_breaker([(5, True), (5, True)])['results'] == ['success', 'success']
    # order: events, size, threshold, cooldown, then entries (shape, time, ok, order)
    _raises(TypeError, EV, m.replay_breaker, L([1]), I(1), I(1))
    _raises(ValueError, TH, m.replay_breaker, [1], I(1), I(1))
    _raises(ValueError, CD, m.replay_breaker, [1], 1, I(1))
    _raises(ValueError, PR, m.replay_breaker, [1], 1, 1)
    _raises(ValueError, TM, m.replay_breaker, [(I(1), 1)], 1, 1)
    _raises(ValueError, OKM, m.replay_breaker, [(5, 1), (4, True)], 1, 1)       # before the order check
    _raises(ValueError, 'times must not decrease', m.replay_breaker, [(5, True), (4, True), (3, 1)], 1, 1)


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


def test_result_is_fresh_and_events_unchanged():
    ev = [(0, False), (1, True)]
    r = mod.replay_breaker(ev)
    r['results'].append('x')
    assert ev == [(0, False), (1, True)]
    assert mod.replay_breaker(ev)['results'] == ['failure', 'success']


MUTANTS = [
    ("type(events) not in (list, tuple)", "not isinstance(events, (list, tuple))"),
    ("len(events) > MAX_EVENTS", "len(events) >= MAX_EVENTS"),
    ("MAX_EVENTS = 100", "MAX_EVENTS = 101"),
    ("type(e) not in (list, tuple) or len(e) != 2", "not isinstance(e, (list, tuple)) or len(e) != 2"),
    ("or len(e) != 2", "or len(e) > 2"),
    ("or len(e) != 2", "or len(e) < 2"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(threshold, 1, 10", "_int(threshold, 0, 10"),
    ("_int(threshold, 1, 10", "_int(threshold, 1, 11"),
    ("_int(cooldown, 1, 1000", "_int(cooldown, 0, 1000"),
    ("_int(cooldown, 1, 1000", "_int(cooldown, 1, 1001"),
    ("_int(t, 0, MAX_TIME", "_int(t, 1, MAX_TIME"),
    ("MAX_TIME = 1000000", "MAX_TIME = 1000001"),
    ("type(ok) is not bool", "not isinstance(ok, int)"),
    ("type(ok) is not bool", "False"),
    ("if t < last:", "if t <= last:"),
    ("if t < last:", "if False:"),
    ("last = t", "last = 0"),
    ("threshold=3", "threshold=2"),
    ("cooldown=10", "cooldown=11"),
    ("cooldown=10", "cooldown=9"),
    ("t - opened_at < cooldown", "t - opened_at <= cooldown"),
    ("t - opened_at < cooldown", "t - opened_at < cooldown - 1"),
    ("state == 'open' and t - opened_at", "t - opened_at"),
    ("fails + 1 >= threshold", "fails + 1 > threshold"),
    ("fails + 1 >= threshold", "fails >= threshold"),
    ("elif probe or", "elif"),
    ("if ok:\n            state, fails = 'closed', 0", "if ok:\n            state = 'closed'"),
    ("state, fails, opened_at, opens = 'open', 0, t, opens + 1", "state, fails, opened_at, opens = 'open', 0, t, opens"),
    ("state, fails, opened_at, opens = 'open', 0, t, opens + 1", "state, fails, opened_at, opens = 'open', 0, opened_at, opens + 1"),
    ("            fails += 1", "            fails += 2"),
    ("            continue\n        probe", "            pass\n        probe"),
    ("'success' if ok else 'failure'", "'failure' if ok else 'success'"),
    ("state, fails, opened_at, opens, results = 'closed', 0, 0, 0, []", "state, fails, opened_at, opens, results = 'open', 0, 0, 0, []"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
