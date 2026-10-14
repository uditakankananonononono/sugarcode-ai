"""Additive hardening for row 1921, Title: Heritage Studies.

New-file hardening on top of the graded pair test for row 1921.
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

from sugarcode.extra_doc import heritage_studies as mod

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
    baseline = {}
    declines = {}
    for site, region, care in rows:
        if site not in baseline:
            baseline[site] = care
            declines[site] = 0
        elif care < baseline[site]:
            declines[site] += 1
    steady = sorted(s for s in declines if declines[s] == 0)
    worst = None
    if declines:
        top = max(declines.values())
        supply = list(dict.fromkeys(s for s, _r, _c in rows))
        worst = next(s for s in supply if declines.get(s) == top)
    return {'total': len(rows), 'declines': declines,
            'steady': steady, 'worst': worst}

def battery(m):
    # a worst tie ignores alphabetical order
    r = m.gauge_care([('z', 'p', 5), ('z', 'q', 3),
                      ('a', 's', 5), ('a', 't', 3)])
    assert r['worst'] == 'z'


    rng = random.Random(51921)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.gauge_care(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for site in declines:',
     '    for site in sorted(declines):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
