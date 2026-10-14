"""Additive hardening for row 1903, Title: Anthropology of Religion.

New-file hardening on top of the graded pair test for row 1903.
Adds an independent oracle battery (never iterating the
implementation's dicts), discriminating first-supplied tie
pins, a first-bad-row error pin, dict insertion-order pins,
and added mutants (including reversed-enumerate validation).
Depends on the graded module and the graded test file; removes
nothing.
"""
import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import anthropology_of_religion as mod

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
    records = 0
    holders = []
    best = 0
    totals = {}
    for tribe, rite, duration in rows:
        if duration > best:
            records += 1
            holders.append(rite)
            best = duration
        if tribe not in totals:
            totals[tribe] = 0
        totals[tribe] += duration
    top = max(totals.values())
    supply = list(dict.fromkeys(t for t, _r, _d in rows))
    enduring = next(t for t in supply if totals[t] == top)
    return {'total': len(rows), 'records': records, 'holders': holders,
            'longest': holders[-1], 'totals': totals, 'enduring': enduring}

def battery(m):
    # an enduring tie ignores alphabetical order
    r = m.record_rites([('z', 'r1', 5), ('a', 'r2', 5)])
    assert r['enduring'] == 'z'

    with pytest.raises(ValueError) as info:
        m.record_rites([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1903)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.record_rites(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for tribe in totals:',
     '    for tribe in sorted(totals):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
