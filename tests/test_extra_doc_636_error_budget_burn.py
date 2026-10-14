import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import error_budget_burn as mod

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
    assert mod.SCOPE == 'PARTIAL: error budget arithmetic over supplied counts, no real measurement'
    assert len(mod.NOT_CLAIMED) >= 4 and 'time windows' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(t, f, s, g):
    """Independent: Fractions and floor via int()."""
    allowed = int(Fraction(t * (100 - s), 100))
    return {'allowed': allowed, 'remaining': allowed - f, 'exhausted': f > allowed,
            'burn_permille': None if allowed == 0 else int(Fraction(f * 1000, allowed)),
            'freeze': f > 0 and Fraction(f, 1) >= Fraction(allowed * g, 100)}


def _core(m):
    assert m.budget_status(1000, 5) == {'allowed': 10, 'remaining': 5, 'exhausted': False, 'burn_permille': 500, 'freeze': False}
    assert m.budget_status(1000, 8) == {'allowed': 10, 'remaining': 2, 'exhausted': False, 'burn_permille': 800, 'freeze': True}
    assert m.budget_status(1000, 7)['freeze'] is False
    assert m.budget_status(1000, 10) == {'allowed': 10, 'remaining': 0, 'exhausted': False, 'burn_permille': 1000, 'freeze': True}
    assert m.budget_status(1000, 11) == {'allowed': 10, 'remaining': -1, 'exhausted': True, 'burn_permille': 1100, 'freeze': True}
    assert m.budget_status(1000, 0) == {'allowed': 10, 'remaining': 10, 'exhausted': False, 'burn_permille': 0, 'freeze': False}
    # allowed rounds down: 150 * 1 // 100 = 1; 99 * 1 // 100 = 0
    assert m.budget_status(150, 0)['allowed'] == 1
    assert m.budget_status(199, 0)['allowed'] == 1
    assert m.budget_status(99, 0)['allowed'] == 0
    assert m.budget_status(99, 0) == {'allowed': 0, 'remaining': 0, 'exhausted': False, 'burn_permille': None, 'freeze': False}
    assert m.budget_status(99, 1) == {'allowed': 0, 'remaining': -1, 'exhausted': True, 'burn_permille': None, 'freeze': True}
    assert m.budget_status(100, 1, 100) == {'allowed': 0, 'remaining': -1, 'exhausted': True, 'burn_permille': None, 'freeze': True}
    assert m.budget_status(1000, 3, 1)['allowed'] == 990
    assert m.budget_status(1000, 3, 90)['allowed'] == 100
    assert m.budget_status(1000, 80, 90) ['freeze'] is True and m.budget_status(1000, 79, 90)['freeze'] is False
    # gate default 80 vs 79/81 and gate 100: freeze only at or over allowed
    assert m.budget_status(1000, 80, 90, 100)['freeze'] is False and m.budget_status(1000, 100, 90, 100)['freeze'] is True
    assert m.budget_status(1000, 50, 90, 50)['freeze'] is True and m.budget_status(1000, 49, 90, 50)['freeze'] is False
    assert m.budget_status(1000, 5, 99, 1)['freeze'] is True
    assert m.budget_status(1000000, 1000000, 1)['burn_permille'] == 1000000 * 1000 // 990000
    assert m.budget_status(1, 1, 99, 1)['exhausted'] is True
    assert m.budget_status(1000, 1000)['remaining'] == -990
    # default slo 99: with 1000 requests and slo 98 allowed would be 20
    assert m.budget_status(1000, 15)['exhausted'] is True and m.budget_status(1000, 15, 98)['exhausted'] is False
    # burn rounds down
    assert m.budget_status(1000, 1)['burn_permille'] == 100
    assert m.budget_status(300, 1)['burn_permille'] == 333
    rng = random.Random(636)
    for _ in range(800):
        t = rng.choice([1, 2, 99, 100, 101, 1000, rng.randint(1, 1000000)])
        f = rng.choice([0, t, rng.randint(0, t), rng.randint(0, min(t, 30))])
        s, g = rng.randint(1, 100), rng.randint(1, 100)
        assert m.budget_status(t, f, s, g) == _oracle(t, f, s, g), (t, f, s, g)


def _late(m):
    TT = 'total must be a nonbool integer between 1 and 1000000'
    FF = 'failed must be a nonbool integer between 0 and 1000000'
    SS = 'slo_percent must be a nonbool integer between 1 and 100'
    GG = 'gate_percent must be a nonbool integer between 1 and 100'
    FX = 'failed must not exceed total'
    BAD = (True, False, 1.0, '1', None, I(5), LyingI(5), LyingI(10 ** 30), I(10 ** 30), [5], (5,))
    for bad in (0, -1, 1000001) + BAD:
        _raises(ValueError, TT, m.budget_status, bad, 0)
    for bad in (-1, 1000001) + BAD:
        _raises(ValueError, FF, m.budget_status, 1000000, bad)
    for bad in (0, 101, -1) + BAD:
        _raises(ValueError, SS, m.budget_status, 10, 0, bad)
        _raises(ValueError, GG, m.budget_status, 10, 0, 99, bad)
    _raises(ValueError, FX, m.budget_status, 5, 6)
    _raises(ValueError, FX, m.budget_status, 1, 2, 50, 50)
    assert m.budget_status(1000000, 1000000)['remaining'] == -990000
    assert m.budget_status(10, 0, 1, 1)['allowed'] == 9 and m.budget_status(10, 0, 100, 100)['allowed'] == 0
    assert m.budget_status(1000, 0, 1)['allowed'] == 990 and m.budget_status(1000, 0, 100)['allowed'] == 0
    # order: total, failed, slo, gate, then failed vs total
    _raises(ValueError, TT, m.budget_status, I(1), I(1), I(1), I(1))
    _raises(ValueError, FF, m.budget_status, 1, I(1), I(1), I(1))
    _raises(ValueError, SS, m.budget_status, 1, 1, I(1), I(1))
    _raises(ValueError, GG, m.budget_status, 1, 1, 1, I(1))
    _raises(ValueError, GG, m.budget_status, 1, 5, 1, 0)       # gate checked before failed > total
    _raises(ValueError, FF, m.budget_status, 1, 1000001)       # failed range before failed > total
    _raises(ValueError, TT, m.budget_status, 0, 5)


class I(int):
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
    ("MAX_TOTAL = 1000000", "MAX_TOTAL = 999999"),
    ("MAX_TOTAL = 1000000", "MAX_TOTAL = 1000001"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(total, 1, MAX_TOTAL", "_int(total, 0, MAX_TOTAL"),
    ("_int(failed, 0, MAX_TOTAL", "_int(failed, 1, MAX_TOTAL"),
    ("_int(slo_percent, 1, 100", "_int(slo_percent, 0, 100"),
    ("_int(slo_percent, 1, 100", "_int(slo_percent, 1, 101"),
    ("_int(gate_percent, 1, 100", "_int(gate_percent, 0, 100"),
    ("_int(gate_percent, 1, 100", "_int(gate_percent, 1, 101"),
    ("slo_percent=99", "slo_percent=98"),
    ("slo_percent=99", "slo_percent=100"),
    ("gate_percent=80", "gate_percent=79"),
    ("gate_percent=80", "gate_percent=81"),
    ("if failed > total:", "if failed >= total:"),
    ("if failed > total:", "if False:"),
    ("total * (100 - slo_percent) // 100", "(total * (100 - slo_percent) + 99) // 100"),
    ("total * (100 - slo_percent) // 100", "total * (99 - slo_percent) // 100"),
    ("'remaining': allowed - failed", "'remaining': failed - allowed"),
    ("'exhausted': failed > allowed", "'exhausted': failed >= allowed"),
    ("None if allowed == 0 else", "None if allowed <= 1 else"),
    ("failed * 1000 // allowed", "failed * 100 // allowed"),
    ("failed * 1000 // allowed", "(failed * 1000 + allowed // 2) // allowed"),
    ("failed > 0 and failed * 100 >= allowed * gate_percent", "failed * 100 >= allowed * gate_percent"),
    ("failed > 0 and failed * 100 >= allowed * gate_percent", "failed > 0 and failed * 100 > allowed * gate_percent"),
    ("failed * 100 >= allowed * gate_percent", "failed * 100 >= allowed * 80"),
    ("failed * 100 >= allowed * gate_percent", "failed >= allowed * gate_percent"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
