"""Additive hardening for row 1895, Title: Translation Studies.

New-file hardening on top of the graded pair test for row 1895.
Adds an independent oracle battery (never iterating the
implementation's dicts), a discriminating first-supplied tie
pin, and a sorted(dict) leader-scan mutant. Depends on the
graded module and the graded test file; removes nothing.
"""
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import translation_studies as mod

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
    counts = {}
    low = {}
    high = {}
    for passage, translator, fidelity in rows:
        if passage not in counts:
            counts[passage] = 0
            low[passage] = fidelity
            high[passage] = fidelity
        counts[passage] += 1
        if fidelity < low[passage]:
            low[passage] = fidelity
        if fidelity > high[passage]:
            high[passage] = fidelity
    consensus = sorted(p for p in counts if counts[p] >= 2 and high[p] == low[p])
    disputed = sorted(p for p in counts if high[p] - low[p] >= 6)
    polarizing = None
    if counts:
        top = max(high[p] - low[p] for p in counts)
        supply = list(dict.fromkeys(p for p, _t, _f in rows))
        polarizing = next(p for p in supply
                          if p in counts and high[p] - low[p] == top)
    return {'total': len(rows), 'counts': counts, 'consensus': consensus,
            'disputed': disputed, 'polarizing': polarizing}

def battery(m):
    # a polarizing tie ignores alphabetical order
    r = m.assess_translations([('z', 't1', 1), ('z', 't2', 5),
                               ('a', 't3', 2), ('a', 't4', 6)])
    assert r['polarizing'] == 'z'


    rng = random.Random(51895)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.assess_translations(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for p in counts:',
     '    for p in sorted(counts):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
