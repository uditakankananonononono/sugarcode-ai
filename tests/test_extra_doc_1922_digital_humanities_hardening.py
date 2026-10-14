"""Additive hardening for row 1922, Title: Digital Humanities.

New-file hardening on top of the graded pair test for row 1922.
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

from sugarcode.extra_doc import digital_humanities as mod

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
    nines = {}
    for corpus, tool, gain in rows:
        if corpus not in counts:
            counts[corpus] = 0
            nines[corpus] = 0
        counts[corpus] += 1
        if gain == 9:
            nines[corpus] += 1
    polished = sorted(c for c in counts
                      if counts[c] >= 2 and nines[c] == counts[c])
    most_nines = None
    if nines:
        top = max(nines.values())
        supply = list(dict.fromkeys(c for c, _t, _g in rows))
        most_nines = next(c for c in supply if nines.get(c) == top)
    return {'total': len(rows), 'nines': nines,
            'polished': polished, 'most_nines': most_nines}

def battery(m):
    # a most_nines tie ignores alphabetical order
    r = m.mark_flawless([('z', 't', 9), ('z', 'u', 9),
                         ('a', 'v', 9), ('a', 'w', 9)])
    assert r['most_nines'] == 'z'


    rng = random.Random(51922)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.mark_flawless(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for corpus in nines:',
     '    for corpus in sorted(nines):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
