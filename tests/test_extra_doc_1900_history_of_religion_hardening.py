"""Additive hardening for row 1900, Title: History of Religion.

New-file hardening on top of the graded pair test for row 1900.
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

from sugarcode.extra_doc import history_of_religion as mod

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
    for era, event, significance in rows:
        if era not in totals:
            totals[era] = 0
            counts[era] = 0
        totals[era] += significance
        counts[era] += 1
    averages = {}
    for era in totals:
        averages[era] = totals[era] // counts[era]
    golden = sorted(era for era in averages if averages[era] >= 7)
    dark = sorted(era for era in averages if averages[era] <= 3)
    top = max(averages.values())
    supply = list(dict.fromkeys(e for e, _v, _s in rows))
    zenith = next(e for e in supply if averages[e] == top)
    return {'total': len(rows), 'averages': averages, 'golden': golden,
            'dark': dark, 'zenith': zenith}

def battery(m):
    # a zenith tie ignores alphabetical order
    r = m.chart_eras([('z', 'e1', 5), ('a', 'e2', 5)])
    assert r['zenith'] == 'z'

    with pytest.raises(ValueError) as info:
        m.chart_eras([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1900)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.chart_eras(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for era in averages:',
     '    for era in sorted(averages):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
