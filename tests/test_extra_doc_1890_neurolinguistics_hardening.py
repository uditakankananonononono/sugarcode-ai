"""Additive hardening for row 1890, Title: Neurolinguistics.

New-file hardening on top of the graded pair test for row 1890.
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

from sugarcode.extra_doc import neurolinguistics as mod

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
    activators = {}
    signal_sum = {}
    for region, task, signal in rows:
        if region not in activators:
            activators[region] = {}
            signal_sum[region] = 0
        if signal >= 5:
            activators[region][task] = True
        signal_sum[region] += signal
    engaged = {}
    for region in activators:
        engaged[region] = len(activators[region])
    hot = sorted(region for region in engaged if engaged[region] >= 3)
    cold = sorted(region for region in engaged if engaged[region] == 0)
    top = max(signal_sum.values())
    supply = list(dict.fromkeys(r for r, _t, _s in rows))
    busiest = next(r for r in supply if signal_sum[r] == top)
    return {'total': len(rows), 'engaged': engaged, 'hot': hot,
            'cold': cold, 'signal': signal_sum, 'busiest': busiest}

def battery(m):
    # a busiest tie ignores alphabetical order
    r = m.map_activation([('z', 't1', 9), ('a', 't2', 9)])
    assert r['busiest'] == 'z'

    rng = random.Random(1890)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.map_activation(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for region in signal_sum:',
     '    for region in sorted(signal_sum):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
