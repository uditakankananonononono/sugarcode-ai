"""Additive hardening for row 1902, Title: Psychology of Religion.

New-file hardening on top of the graded pair test for row 1902.
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

from sugarcode.extra_doc import psychology_of_religion as mod

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
    marks = {}
    counts = {}
    for subject, experience, intensity in rows:
        if subject not in marks:
            marks[subject] = {}
            counts[subject] = 0
        marks[subject][intensity] = True
        counts[subject] += 1
    gaps = {}
    for subject in marks:
        vals = sorted(marks[subject], reverse=True)
        if len(vals) >= 2:
            gaps[subject] = vals[0] - vals[1]
        else:
            gaps[subject] = 0
    spiked = sorted(s for s in gaps if gaps[s] >= 5)
    level = sorted(s for s in gaps if counts[s] >= 2 and gaps[s] <= 1)
    top = max(gaps.values())
    supply = list(dict.fromkeys(s for s, _e, _i in rows))
    sharpest = next(s for s in supply if gaps[s] == top)
    return {'total': len(rows), 'gaps': gaps, 'spiked': spiked,
            'level': level, 'sharpest': sharpest}

def battery(m):
    # a sharpest tie ignores alphabetical order
    r = m.probe_subjects([('z', 'e1', 1), ('z', 'e2', 6),
                          ('a', 'e3', 2), ('a', 'e4', 7)])
    assert r['sharpest'] == 'z'

    with pytest.raises(ValueError) as info:
        m.probe_subjects([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1902)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.probe_subjects(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for subject in gaps:',
     '    for subject in sorted(gaps):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
