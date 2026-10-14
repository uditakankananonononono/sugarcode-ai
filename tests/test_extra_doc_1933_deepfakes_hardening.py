"""Additive hardening for row 1933, Title: Deepfakes.

New-file hardening on top of the graded pair test for row 1933.
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

from sugarcode.extra_doc import deepfakes as mod

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
    firsts = {}
    anchors = {}
    supplied = {}
    for frame, model, score in rows:
        if model not in firsts:
            firsts[model] = score
            anchors[model] = 0
            supplied[model] = 0
        supplied[model] += 1
        if score == firsts[model]:
            anchors[model] += 1
    steady = sorted(m for m in anchors if anchors[m] == supplied[m])
    firmest = None
    if anchors:
        top = max(anchors.values())
        supply = list(dict.fromkeys(m for _f, m, _s in rows))
        firmest = next(m for m in supply if anchors.get(m) == top)
    return {'total': len(rows), 'anchors': anchors,
            'steady': steady, 'firmest': firmest}

def battery(m):
    # a firmest tie ignores alphabetical order
    r = m.anchor_counts([('f1', 'z', 9), ('f2', 'z', 9),
                         ('f3', 'a', 9), ('f4', 'a', 9)])
    assert r['firmest'] == 'z'


    rng = random.Random(51933)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.anchor_counts(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for model in anchors:',
     '    for model in sorted(anchors):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
