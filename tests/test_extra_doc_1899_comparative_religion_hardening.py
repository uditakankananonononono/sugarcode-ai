"""Additive hardening for row 1899, Title: Comparative Religion.

New-file hardening on top of the graded pair test for row 1899.
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

from sugarcode.extra_doc import comparative_religion as mod

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
    hist = {}
    for tradition, ritual, frequency in rows:
        if tradition not in hist:
            hist[tradition] = {}
        hist[tradition][frequency] = hist[tradition].get(frequency, 0) + 1
    modes = {}
    for tradition in hist:
        best_value = None
        best_count = 0
        for frequency in sorted(hist[tradition]):
            if hist[tradition][frequency] > best_count:
                best_value = frequency
                best_count = hist[tradition][frequency]
        modes[tradition] = best_value
    canonical = sorted(t for t in hist if max(hist[t].values()) >= 3)
    unrepeated = sorted(t for t in hist if len(hist[t]) >= 2 and max(hist[t].values()) == 1)
    top = max(max(hist[t].values()) for t in hist)
    supply = list(dict.fromkeys(t for t, _r, _f in rows))
    typical = next(t for t in supply if max(hist[t].values()) == top)
    return {'total': len(rows), 'modes': modes, 'canonical': canonical,
            'unrepeated': unrepeated, 'typical': typical}

def battery(m):
    # a typical tie ignores alphabetical order
    r = m.compare_rituals([('z', 'r1', 5), ('z', 'r2', 5),
                           ('a', 'r3', 5), ('a', 'r4', 5)])
    assert r['typical'] == 'z'

    with pytest.raises(ValueError) as info:
        m.compare_rituals([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1899)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.compare_rituals(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    typical = None\n    for tradition in hist:',
     '    typical = None\n    for tradition in sorted(hist):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
