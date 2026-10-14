import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import alert_rules as mod

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
    assert mod.SCOPE == 'PARTIAL: threshold rule replay over supplied readings, no notifications sent'
    assert len(mod.NOT_CLAIMED) >= 4 and 'delivering notifications' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle_one(readings, thr, fc, hyst):
    """Independent: jump from event to event by searching forward, no running counter."""
    n, i, fired, resolved, state = len(readings), 0, [], [], 'ok'
    while i < n:
        if state == 'ok':
            hit = None
            for j in range(i + fc - 1, n):
                if all(readings[x] > thr for x in range(j - fc + 1, j + 1)):
                    hit = j
                    break
            if hit is None:
                break
            fired.append(hit)
            state, i = 'firing', hit + 1
        else:
            hit = None
            for k in range(i, n):
                if readings[k] <= thr - hyst:
                    hit = k
                    break
            if hit is None:
                break
            resolved.append(hit)
            state, i = 'ok', hit + 1
    return {'fired': fired, 'resolved': resolved, 'state': state}


def _core(m):
    rd = [1, 5, 6, 7, 2, 8, 9, 3, 9, 9, 9]
    r = m.evaluate_alerts([('hi', 4, 2), ('one', 8, 1), ('never', 9, 3)], rd)
    assert r['rules']['hi'] == {'fired': [2, 6, 9], 'resolved': [4, 7], 'state': 'firing'}
    assert r['rules']['one'] == {'fired': [6, 8], 'resolved': [7], 'state': 'firing'}
    assert r['rules']['never'] == {'fired': [], 'resolved': [], 'state': 'ok'}
    assert r['firing'] == ['hi', 'one']
    assert r['firing'] == sorted(n for n, x in r['rules'].items() if x['state'] == 'firing')
    assert m.evaluate_alerts([('hi', 4, 2)], rd) == {'rules': {'hi': {'fired': [2, 6, 9], 'resolved': [4, 7], 'state': 'firing'}}, 'firing': ['hi']}
    # strictly greater: equal to the threshold does not count
    assert m.evaluate_alerts([('a', 5, 1)], [5, 5, 5])['rules']['a'] == {'fired': [], 'resolved': [], 'state': 'ok'}
    assert m.evaluate_alerts([('a', 5, 1)], [6])['rules']['a'] == {'fired': [0], 'resolved': [], 'state': 'firing'}
    assert m.evaluate_alerts([('a', 5, 2)], [6, 5, 6])['rules']['a']['fired'] == []              # a break resets the streak
    assert m.evaluate_alerts([('a', 5, 2)], [6, 6])['rules']['a']['fired'] == [1]
    assert m.evaluate_alerts([('a', 5, 3)], [6, 6, 6, 6, 6, 6])['rules']['a'] == {'fired': [2], 'resolved': [], 'state': 'firing'}
    # resolve: at or below threshold counts when hysteresis is 0, readings above stay firing
    assert m.evaluate_alerts([('a', 5, 1)], [6, 5, 6])['rules']['a'] == {'fired': [0, 2], 'resolved': [1], 'state': 'firing'}
    assert m.evaluate_alerts([('a', 5, 1)], [6, 6, 6, 4])['rules']['a'] == {'fired': [0], 'resolved': [3], 'state': 'ok'}
    # hysteresis: must drop to threshold - hysteresis
    assert m.evaluate_alerts([('a', 5, 1)], [6, 5, 4, 3], 2)['rules']['a'] == {'fired': [0], 'resolved': [3], 'state': 'ok'}
    assert m.evaluate_alerts([('a', 5, 1)], [6, 5, 4, 3], 1)['rules']['a']['resolved'] == [2]
    assert m.evaluate_alerts([('a', 5, 1)], [6, 5, 4, 3], 0)['rules']['a']['resolved'] == [1]
    assert m.evaluate_alerts([('a', 5, 1)], [6, 0], 5)['rules']['a']['resolved'] == [1]
    assert m.evaluate_alerts([('a', 5, 1)], [6, 1], 5)['rules']['a']['resolved'] == []
    assert m.evaluate_alerts([('a', 5, 1)], [6, 1000], 1000)['rules']['a']['resolved'] == []         # threshold - hysteresis is negative
    # the streak restarts after a resolve
    assert m.evaluate_alerts([('a', 5, 2)], [6, 6, 0, 6, 0, 6, 6])['rules']['a'] == {'fired': [1, 6], 'resolved': [2], 'state': 'firing'}
    assert m.evaluate_alerts([('a', 5, 2)], [6, 6, 6, 6])['rules']['a']['fired'] == [1]              # no refire while firing
    assert m.evaluate_alerts([('a', 5, 2)], [])['rules']['a'] == {'fired': [], 'resolved': [], 'state': 'ok'}
    assert m.evaluate_alerts([('a', 0, 1)], [0, 1000000, 0])['rules']['a'] == {'fired': [1], 'resolved': [2], 'state': 'ok'}
    assert m.evaluate_alerts([('a', 1000000, 1)], [1000000])['rules']['a']['fired'] == []
    assert m.evaluate_alerts([('a', 5, 10)], [9] * 10)['rules']['a']['fired'] == [9]
    assert m.evaluate_alerts([('a', 5, 10)], [9] * 9)['rules']['a']['fired'] == []
    r = m.evaluate_alerts([('b', 5, 1), ('a', 5, 1), ('c', 50, 1)], (6,))
    assert r['firing'] == ['a', 'b'] and list(r['rules']) == ['b', 'a', 'c']
    assert m.evaluate_alerts([('x' * 16, 5, 1)], [6])['firing'] == ['x' * 16]
    assert m.evaluate_alerts([['n', 1, 1]], [2] * 100)['rules']['n']['fired'] == [0]
    assert len(m.evaluate_alerts([('r%d' % i, 1, 1) for i in range(20)], [2])['firing']) == 20
    rng = random.Random(633)
    for _ in range(600):
        rd = [rng.randint(0, 10) for _ in range(rng.randint(0, 30))]
        rules = [('r%d' % k, rng.randint(0, 9), rng.randint(1, 4)) for k in range(rng.randint(1, 4))]
        h = rng.choice((0, 0, 1, 2, 5, 1000))
        got = m.evaluate_alerts(rules, rd, h)
        for name, thr, fc in rules:
            assert got['rules'][name] == _oracle_one(rd, thr, fc, h), (rd, thr, fc, h)


def _late(m):
    RL = 'rules must be a list or tuple'
    SZ = 'rules must contain between 1 and 20 entries'
    RD = 'readings must be a list or tuple'
    HY = 'hysteresis must be a nonbool integer between 0 and 1000'
    ER = 'each rule must be a (name, threshold, for_count) triple'
    RN = 'rule names must be strings of 1 to 16 characters'
    TH = 'threshold must be a nonbool integer between 0 and 1000000'
    FC = 'for_count must be a nonbool integer between 1 and 10'
    RV = 'readings must be nonbool integers between 0 and 1000000'
    good = ('a', 5, 1)
    for bad in ('ab', None, 5, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, RL, m.evaluate_alerts, bad, [])
    _raises(TypeError, RL, m.evaluate_alerts, L([good] * 21), [])
    _raises(ValueError, SZ, m.evaluate_alerts, [], [])
    _raises(ValueError, SZ, m.evaluate_alerts, [('r%d' % i, 1, 1) for i in range(21)], [])
    for bad in ('ab', None, 5, {}, L([1]), T([1]), L(), T()):
        _raises(TypeError, RD, m.evaluate_alerts, [good], bad)
    _raises(TypeError, RD, m.evaluate_alerts, [good], L([1] * 101))
    _raises(ValueError, 'readings must contain at most 100 entries', m.evaluate_alerts, [good], [1] * 101)
    assert m.evaluate_alerts([good], [9] * 100)['rules']['a']['fired'] == [0]
    for bad in (-1, 1001, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, HY, m.evaluate_alerts, [good], [], bad)
    for K in (L, T):
        for bad in (K(good), K(('a', 5))):
            _raises(ValueError, ER, m.evaluate_alerts, [bad], [])
            _raises(ValueError, ER, m.evaluate_alerts, [good, bad], [])
    for bad in ('abc', None, 5, ('a', 5), ('a', 5, 1, 1), ()):
        _raises(ValueError, ER, m.evaluate_alerts, [bad], [])
        _raises(ValueError, ER, m.evaluate_alerts, [good, bad], [])
    for bad in ('', 'x' * 17, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, RN, m.evaluate_alerts, [(bad, 5, 1)], [])
        _raises(ValueError, RN, m.evaluate_alerts, [good, (bad, 5, 1)], [])
    _raises(ValueError, 'duplicate rule name', m.evaluate_alerts, [good, good], [])
    _raises(ValueError, 'duplicate rule name', m.evaluate_alerts, [good, ('b', 1, 1), ('a', 1, 1)], [])
    for bad in (-1, 1000001, True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TH, m.evaluate_alerts, [('b', bad, 1)], [])
        _raises(ValueError, TH, m.evaluate_alerts, [good, ('b', bad, 1)], [])
    for bad in (0, 11, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, FC, m.evaluate_alerts, [('b', 5, bad)], [])
        _raises(ValueError, FC, m.evaluate_alerts, [good, ('b', 5, bad)], [])
    for bad in (-1, 1000001, True, False, 1.0, '1', None, [1], I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, RV, m.evaluate_alerts, [good], [bad])
        _raises(ValueError, RV, m.evaluate_alerts, [good], [1, bad])
        _raises(ValueError, RV, m.evaluate_alerts, [good], (1, 2, bad))
    # order: rules, size, readings container, readings size, hysteresis, rules rows (shape, name, duplicate, threshold, for_count), readings values
    _raises(TypeError, RL, m.evaluate_alerts, L([1]), L([1]), I(1))
    _raises(ValueError, SZ, m.evaluate_alerts, [], L([1]), I(1))
    _raises(TypeError, RD, m.evaluate_alerts, [1], L([1]), I(1))
    _raises(ValueError, 'readings must contain at most 100 entries', m.evaluate_alerts, [1], [1] * 101, I(1))
    _raises(ValueError, HY, m.evaluate_alerts, [1], [I(1)], I(1))
    _raises(ValueError, ER, m.evaluate_alerts, [1], [I(1)], 1)
    _raises(ValueError, RN, m.evaluate_alerts, [(S('a'), I(1), I(1))], [I(1)])
    _raises(ValueError, TH, m.evaluate_alerts, [('a', I(1), I(1))], [I(1)])
    _raises(ValueError, FC, m.evaluate_alerts, [('a', 1, I(1))], [I(1)])
    _raises(ValueError, RV, m.evaluate_alerts, [('a', 1, 1)], [I(1)])


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


def test_result_is_fresh_and_inputs_unchanged():
    rules, rd = [('a', 1, 1)], [2]
    r = mod.evaluate_alerts(rules, rd)
    r['rules']['a']['fired'].append(99)
    r['firing'].append('zzz')
    assert rules == [('a', 1, 1)] and rd == [2]
    assert mod.evaluate_alerts(rules, rd)['rules']['a']['fired'] == [0]


MUTANTS = [
    ("type(rules) not in (list, tuple)", "not isinstance(rules, (list, tuple))"),
    ("type(readings) not in (list, tuple)", "not isinstance(readings, (list, tuple))"),
    ("not 1 <= len(rules) <= MAX_RULES", "not 0 <= len(rules) <= MAX_RULES"),
    ("not 1 <= len(rules) <= MAX_RULES", "not 1 <= len(rules) < MAX_RULES"),
    ("MAX_RULES = 20", "MAX_RULES = 21"),
    ("len(readings) > MAX_READINGS", "len(readings) >= MAX_READINGS"),
    ("MAX_READINGS = 100", "MAX_READINGS = 101"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(hysteresis, 0, 1000", "_int(hysteresis, 1, 1000"),
    ("_int(hysteresis, 0, 1000", "_int(hysteresis, 0, 1001"),
    ("hysteresis=0", "hysteresis=1"),
    ("type(r) not in (list, tuple) or len(r) != 3", "not isinstance(r, (list, tuple)) or len(r) != 3"),
    ("or len(r) != 3", "or len(r) > 3"),
    ("or len(r) != 3", "or len(r) < 3"),
    ("type(name) is not str", "not isinstance(name, str)"),
    ("not 1 <= len(name) <= 16", "not 0 <= len(name) <= 16"),
    ("not 1 <= len(name) <= 16", "not 1 <= len(name) <= 17"),
    ("not 1 <= len(name) <= 16", "not 1 <= len(name) < 16"),
    ("if name in names:", "if False:"),
    ("_int(threshold, 0, 1000000", "_int(threshold, 1, 1000000"),
    ("_int(threshold, 0, 1000000", "_int(threshold, 0, 1000001"),
    ("_int(for_count, 1, 10", "_int(for_count, 0, 10"),
    ("_int(for_count, 1, 10", "_int(for_count, 1, 11"),
    ("_int(for_count, 1, 10", "_int(for_count, 1, 9"),
    ("_int(v, 0, 1000000, 'readings", "_int(v, 1, 1000000, 'readings"),
    ("_int(v, 0, 1000000, 'readings", "_int(v, 0, 1000001, 'readings"),
    ("v <= threshold - hysteresis", "v < threshold - hysteresis"),
    ("v <= threshold - hysteresis", "v <= threshold + hysteresis"),
    ("v <= threshold - hysteresis", "v <= threshold"),
    ("elif v > threshold:", "elif v >= threshold:"),
    ("streak += 1", "streak += 2"),
    ("if streak == for_count:", "if streak >= for_count + 1:"),
    ("if streak == for_count:", "if streak == for_count - 1:"),
    ("firing, streak = True, 0", "firing, streak = True, streak"),
    ("            else:\n                streak = 0", "            else:\n                pass"),
    ("fired.append(i)", "fired.append(i + 1)"),
    ("resolved.append(i)", "resolved.append(i + 1)"),
    ("'firing' if firing else 'ok'", "'ok' if firing else 'firing'"),
    ("sorted(n for n, r in out.items()", "list(n for n, r in out.items()"),
    ("r['state'] == 'firing'", "r['state'] == 'ok'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
