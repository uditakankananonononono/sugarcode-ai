"""Additive hardening for row 1907, Title: Art History.

New-file hardening on top of the graded pair test for row 1907.
Adds an independent oracle battery (never iterating the
implementation's dicts), discriminating first-supplied tie
pins, and added mutants. Depends on the graded module and the
graded test file; removes nothing.
"""
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import art_history as mod

SRC = pathlib.Path(mod.__file__).read_text()

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _survives(battery, old, new):
    doc_end = SRC.index('"""', 3) + 3
    assert SRC.find(old) > doc_end, 'mutation target must be code, not the docstring'
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    code = compile(mutated, 'mutant', 'exec')
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


def _expected(rows):
    tops = {}
    masters = {}
    for work, period, merit in rows:
        if period not in tops or merit > tops[period]:
            tops[period] = merit
            masters[period] = work
    celebrated = sorted(p for p in tops if tops[p] >= 8)
    thin = sorted(p for p in tops if tops[p] <= 3)
    top = max(tops.values())
    supply = list(dict.fromkeys(p for _w, p, _m in rows))
    finest = next(p for p in supply if tops[p] == top)
    return {'total': len(rows), 'masters': masters,
            'celebrated': celebrated, 'thin': thin, 'finest': finest}

def battery(m):
    # a finest tie ignores alphabetical order
    r = m.crown_periods([('w1', 'z', 5), ('w2', 'a', 5)])
    assert r['finest'] == 'z'

    rng = random.Random(1907)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.crown_periods(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for period in tops:',
     '    for period in sorted(tops):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
