import datetime
import itertools
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import capacity_planning as mod

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
    signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
    return True


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _expected(cur, g, periods, cap):
    demand, rounded, first = [], [], None
    if cur > cap:
        first = 0
    for t in range(1, periods + 1):
        num, den = cur * (100 + g) ** t, 100 ** t
        rounded.append((num + den - 1) // den)
        if first is None and num > cap * den:
            first = t
    return {'demand': rounded, 'headroom': [cap - d for d in rounded], 'first_breach_period': first}


def _core(m):
    assert m.capacity_plan(100, 10, 3, 120) == {'demand': [110, 121, 134], 'headroom': [10, -1, -14], 'first_breach_period': 2}
    assert m.capacity_plan(100, 0, 3, 100) == {'demand': [100] * 3, 'headroom': [0] * 3, 'first_breach_period': None}
    assert m.capacity_plan(101, 0, 1, 100)['first_breach_period'] == 0
    assert m.capacity_plan(1, 1, 2, 1)['demand'] == [2, 2] and m.capacity_plan(1, 1, 2, 1)['first_breach_period'] == 1
    rng = random.Random(641)
    for _ in range(300):
        a = (rng.randint(1, 1000000), rng.choice([0, 1, 3, 7, 25, 50, 99, 100, rng.randint(0, 100)]),
             rng.randint(1, 24), rng.choice([1, 50, 10 ** 6, 10 ** 9, rng.randint(1, 10 ** 9)]))
        assert m.capacity_plan(*a) == _expected(*a)
    a = (1000000, 100, 24, 1000000000)
    assert m.capacity_plan(*a) == _expected(*a)
    # exact boundary: demand exactly equal to capacity is not a breach
    assert m.capacity_plan(100, 100, 1, 200)['first_breach_period'] is None
    assert m.capacity_plan(100, 100, 1, 199)['first_breach_period'] == 1
    for bad in (0, 1000001, True, 1.0, '1'):
        _raises(ValueError, 'current must be a nonbool integer between 1 and 1000000', m.capacity_plan, bad, 1, 1, 1)
    for bad in (-1, 101, True, 1.5):
        _raises(ValueError, 'growth_percent must be a nonbool integer between 0 and 100', m.capacity_plan, 1, bad, 1, 1)
    for bad in (0, 25, True, 1.0):
        _raises(ValueError, 'periods must be a nonbool integer between 1 and 24', m.capacity_plan, 1, 1, bad, 1)
    for bad in (0, 1000000001, True, 1.0):
        _raises(ValueError, 'capacity must be a nonbool integer between 1 and 1000000000', m.capacity_plan, 1, 1, 1, bad)
    _raises(ValueError, 'current must be a nonbool integer between 1 and 1000000', m.capacity_plan, 0, -1, 99, 0)



class I(int):
    pass


def _late(m):
    _raises(ValueError, 'current must be a nonbool integer between 1 and 1000000', m.capacity_plan, I(5), 1, 1, 1)
    _raises(ValueError, 'growth_percent must be a nonbool integer between 0 and 100', m.capacity_plan, 5, I(1), 1, 1)
    _raises(ValueError, 'periods must be a nonbool integer between 1 and 24', m.capacity_plan, 5, 1, I(1), 1)
    _raises(ValueError, 'capacity must be a nonbool integer between 1 and 1000000000', m.capacity_plan, 5, 1, 1, I(1))


def battery(m):
    _core(m)
    _late(m)

MUTANTS = [
    ('demand > capacity else None', 'demand >= capacity else None'), ('first is None and demand > capacity', 'first is None and demand >= capacity'),
    ('-((-demand.numerator) // demand.denominator)', 'demand.numerator // demand.denominator'),
    ('capacity - d for d', 'd - capacity for d'), ('Fraction(100 + growth_percent, 100)', 'Fraction(growth_percent, 100)'),
    ('Fraction(100 + growth_percent, 100)', 'Fraction(101 + growth_percent, 100)'),
    ('first = 0 if', 'first = 1 if'), ('range(1, periods + 1)', 'range(periods)'),
    ('_int(current, 1, 1000000, ', '_int(current, 1, 1000001, '), ('_int(current, 1, 1000000, ', '_int(current, 0, 1000000, '),
    ('_int(growth_percent, 0, 100, ', '_int(growth_percent, 0, 101, '), ('_int(growth_percent, 0, 100, ', '_int(growth_percent, 1, 100, '),
    ('_int(periods, 1, 24, ', '_int(periods, 1, 25, '), ('_int(periods, 1, 24, ', '_int(periods, 0, 24, '),
    ('_int(capacity, 1, 1000000000, ', '_int(capacity, 1, 1000000001, '), ('_int(capacity, 1, 1000000000, ', '_int(capacity, 0, 1000000000, '),
    ('type(v) is not int', 'isinstance(v, bool) or not isinstance(v, int)'), ('demand *= factor', 'pass'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    battery(mod)
