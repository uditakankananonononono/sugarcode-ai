"""Additive hardening for row 1896, Title: Interpretation Studies.

New-file hardening on top of the graded pair test for row 1896.
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

from sugarcode.extra_doc import interpretation_studies as mod

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
    readings = {}
    for text, reader, clarity in rows:
        if text not in readings:
            readings[text] = []
        readings[text].append(clarity)
    medians = {}
    for text in readings:
        vals = sorted(readings[text])
        medians[text] = vals[(len(vals) - 1) // 2]
    lucid = sorted(t for t in medians if medians[t] >= 7)
    murky = sorted(t for t in medians if medians[t] <= 3)
    top = max(medians.values())
    supply = list(dict.fromkeys(t for t, _r, _c in rows))
    clearest = next(t for t in supply if medians[t] == top)
    return {'total': len(rows), 'medians': medians, 'lucid': lucid,
            'murky': murky, 'clearest': clearest}

def battery(m):
    # a clearest tie ignores alphabetical order
    r = m.gauge_clarity([('z', 'r1', 5), ('a', 'r2', 5)])
    assert r['clearest'] == 'z'

    rng = random.Random(1896)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.gauge_clarity(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for text in medians:',
     '    for text in sorted(medians):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
