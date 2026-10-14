"""Additive hardening for row 1897, Title: Religion.

New-file hardening on top of the graded pair test for row 1897.
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

from sugarcode.extra_doc import religion as mod

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
    totals = {}
    counts = {}
    for tradition, practice, adherents in rows:
        if tradition not in totals:
            totals[tradition] = 0
            counts[tradition] = 0
        totals[tradition] += adherents
        counts[tradition] += 1
    streak_tradition = rows[0][0]
    streak_length = 1
    run_tradition = rows[0][0]
    run_length = 1
    for tradition, practice, adherents in rows[1:]:
        if tradition == run_tradition:
            run_length += 1
        else:
            run_tradition = tradition
            run_length = 1
        if run_length > streak_length:
            streak_tradition = run_tradition
            streak_length = run_length
    widespread = sorted(t for t in counts if counts[t] >= 3)
    top = max(totals.values())
    supply = list(dict.fromkeys(t for t, _p, _a in rows))
    devoted = next(t for t in supply if totals[t] == top)
    return {'total': len(rows), 'totals': totals,
            'streak': {'tradition': streak_tradition, 'length': streak_length},
            'widespread': widespread, 'devoted': devoted}

def battery(m):
    # a devoted tie ignores alphabetical order
    r = m.survey_traditions([('z', 'p1', 5), ('a', 'p2', 5)])
    assert r['devoted'] == 'z'

    rng = random.Random(1897)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.survey_traditions(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for tradition in totals:',
     '    for tradition in sorted(totals):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
