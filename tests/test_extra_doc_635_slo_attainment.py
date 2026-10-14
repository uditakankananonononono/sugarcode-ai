import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import slo_attainment as mod

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


from fractions import Fraction


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: SLO attainment arithmetic over supplied counts, no real measurement'
    assert len(mod.NOT_CLAIMED) >= 4 and 'alerting' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(ws, target):
    """Independent: Fraction arithmetic."""
    g = sum(Fraction(a) for a, _ in ws)
    t = sum(Fraction(b) for _, b in ws)
    return {'met': g / t >= Fraction(target, 100),
            'sli_permille': int((g / t) * 1000),
            'windows_met': sum(1 for a, b in ws if Fraction(a, b) >= Fraction(target, 100)),
            'good_total': int(g), 'event_total': int(t)}


def _core(m):
    assert m.slo_attainment([(99, 100)]) == {'met': True, 'sli_permille': 990, 'windows_met': 1, 'good_total': 99, 'event_total': 100}
    assert m.slo_attainment([(98, 100)]) == {'met': False, 'sli_permille': 980, 'windows_met': 0, 'good_total': 98, 'event_total': 100}
    assert m.slo_attainment([(98, 100)], 98)['met'] is True
    assert m.slo_attainment([(98, 100)], 99)['met'] is False
    assert m.slo_attainment([(0, 1)], 1) == {'met': False, 'sli_permille': 0, 'windows_met': 0, 'good_total': 0, 'event_total': 1}
    assert m.slo_attainment([(1, 1)], 100)['met'] is True
    assert m.slo_attainment([(999, 1000)], 100)['met'] is False
    # pooled vs per window: one bad small window, one big good window
    r = m.slo_attainment([(0, 1), (999, 999)])
    assert r == {'met': True, 'sli_permille': 999, 'windows_met': 1, 'good_total': 999, 'event_total': 1000}
    r = m.slo_attainment([(1, 2), (1, 2)], 50)
    assert r == {'met': True, 'sli_permille': 500, 'windows_met': 2, 'good_total': 2, 'event_total': 4}
    assert m.slo_attainment([(1, 3)], 33)['met'] is True and m.slo_attainment([(1, 3)], 34)['met'] is False
    assert m.slo_attainment([(1, 3)])['sli_permille'] == 333          # rounded down
    assert m.slo_attainment([(2, 3)])['sli_permille'] == 666
    # default target 99: 98.9% fails, 99.0% passes; 25 or 98 would pass the first
    assert m.slo_attainment([(989, 1000)])['met'] is False
    assert m.slo_attainment([(990, 1000)])['met'] is True
    assert m.slo_attainment([(1000000, 1000000)])['event_total'] == 1000000
    assert m.slo_attainment([(1, 1)] * 60)['event_total'] == 60
    assert m.slo_attainment([[5, 5], (5, 5)])['windows_met'] == 2
    assert m.slo_attainment([(0, 1)] * 59 + [(1, 1)]) == {'met': False, 'sli_permille': 16, 'windows_met': 1, 'good_total': 1, 'event_total': 60}
    assert m.slo_attainment([(1, 1), (99, 100), (50, 100)], 99)['windows_met'] == 2
    rng = random.Random(635)
    for _ in range(600):
        tg = rng.randint(1, 100)
        ws = []
        for _k in range(rng.randint(1, 12)):
            t = rng.choice([1, 2, 3, 7, 100, 1000, rng.randint(1, 1000000)])
            ws.append((rng.choice([0, t, rng.randint(0, t), max(0, t - 1)]), t))
        assert m.slo_attainment(ws, tg) == _oracle(ws, tg), (ws, tg)


def _late(m):
    WN = 'windows must be a list or tuple'
    SZ = 'windows must contain 1 to 60 entries'
    TP = 'target_percent must be a nonbool integer between 1 and 100'
    EW = 'each window must be a (good, total) pair'
    TT = 'total must be a nonbool integer between 1 and 1000000'
    GD = 'good must be a nonbool integer between 0 and 1000000'
    GX = 'good must not exceed total'
    ok = (1, 1)
    for bad in ('ab', None, 5, {}, L([ok]), T([ok]), L(), T()):
        _raises(TypeError, WN, m.slo_attainment, bad)
    _raises(TypeError, WN, m.slo_attainment, L([ok] * 61))
    _raises(ValueError, SZ, m.slo_attainment, [])
    _raises(ValueError, SZ, m.slo_attainment, ())
    _raises(ValueError, SZ, m.slo_attainment, [ok] * 61)
    assert m.slo_attainment([ok] * 60)['event_total'] == 60
    for bad in (0, 101, -1, True, False, 1.0, '1', None, I(99), LyingI(99), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TP, m.slo_attainment, [ok], bad)
    assert m.slo_attainment([ok], 1)['met'] and m.slo_attainment([ok], 100)['met']
    for K in (L, T):
        for bad in (K(ok), K((1,))):
            _raises(ValueError, EW, m.slo_attainment, [bad])
            _raises(ValueError, EW, m.slo_attainment, [ok, bad])
    for bad in ('ab', None, 5, (1,), (1, 1, 1), ()):
        _raises(ValueError, EW, m.slo_attainment, [bad])
        _raises(ValueError, EW, m.slo_attainment, [ok, bad])
    for bad in (0, -1, 1000001, True, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, TT, m.slo_attainment, [(0, bad)])
        _raises(ValueError, TT, m.slo_attainment, [ok, (0, bad)])
    for bad in (-1, 1000001, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, GD, m.slo_attainment, [(bad, 1000000)])
        _raises(ValueError, GD, m.slo_attainment, [ok, (bad, 1000000)])
    _raises(ValueError, GX, m.slo_attainment, [(2, 1)])
    _raises(ValueError, GX, m.slo_attainment, [ok, (3, 2)])
    assert m.slo_attainment([(0, 1)])['good_total'] == 0
    # order: windows type, size, target, then per window shape, total, good, good vs total
    _raises(TypeError, WN, m.slo_attainment, L([1]), I(1))
    _raises(ValueError, SZ, m.slo_attainment, [], I(1))
    _raises(ValueError, TP, m.slo_attainment, [1], I(1))
    _raises(ValueError, EW, m.slo_attainment, [1], 5)
    _raises(ValueError, TT, m.slo_attainment, [(I(1), I(1))])
    _raises(ValueError, TT, m.slo_attainment, [(True, 0)])
    _raises(ValueError, GD, m.slo_attainment, [(I(1), 1)])
    _raises(ValueError, GD, m.slo_attainment, [(-1, 0 + 1)])
    _raises(ValueError, GD, m.slo_attainment, [(1000001, 1000000)])


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


MUTANTS = [
    ("type(windows) not in (list, tuple)", "not isinstance(windows, (list, tuple))"),
    ("not 1 <= len(windows) <= MAX_WINDOWS", "not 0 <= len(windows) <= MAX_WINDOWS"),
    ("not 1 <= len(windows) <= MAX_WINDOWS", "not 1 <= len(windows) < MAX_WINDOWS"),
    ("MAX_WINDOWS = 60", "MAX_WINDOWS = 61"),
    ("MAX_TOTAL = 1000000", "MAX_TOTAL = 999999"),
    ("MAX_TOTAL = 1000000", "MAX_TOTAL = 1000001"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(target_percent, 1, 100", "_int(target_percent, 0, 100"),
    ("_int(target_percent, 1, 100", "_int(target_percent, 1, 101"),
    ("target_percent=99", "target_percent=98"),
    ("target_percent=99", "target_percent=100"),
    ("type(w) not in (list, tuple) or len(w) != 2", "not isinstance(w, (list, tuple)) or len(w) != 2"),
    ("or len(w) != 2", "or len(w) > 2"),
    ("or len(w) != 2", "or len(w) < 2"),
    ("_int(total, 1, MAX_TOTAL", "_int(total, 0, MAX_TOTAL"),
    ("_int(good, 0, MAX_TOTAL", "_int(good, 1, MAX_TOTAL"),
    ("if good > total:", "if good >= total:"),
    ("if good > total:", "if False:"),
    ("'met': good_total * 100 >= target_percent * event_total", "'met': good_total * 100 > target_percent * event_total"),
    ("'met': good_total * 100 >= target_percent * event_total", "'met': good_total * 100 >= target_percent * (event_total + 1)"),
    ("good_total * 1000 // event_total", "(good_total * 1000 + event_total // 2) // event_total"),
    ("good_total * 1000 // event_total", "good_total * 1000 // (event_total + 1)"),
    ("'windows_met': sum(1 for g, t in windows if g * 100 >= target_percent * t)", "'windows_met': sum(1 for g, t in windows if g * 100 > target_percent * t)"),
    ("'windows_met': sum(1 for g, t in windows if g * 100 >= target_percent * t)", "'windows_met': sum(1 for g, t in windows if g >= t)"),
    ("good_total = sum(w[0] for w in windows)", "good_total = sum(w[0] for w in windows[:59])"),
    ("event_total = sum(w[1] for w in windows)", "event_total = sum(w[1] for w in windows[1:])"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
