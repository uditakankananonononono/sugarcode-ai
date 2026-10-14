"""Additive hardening for row 1891, Title: Historical Linguistics.

New-file hardening on top of the graded pair test for row 1891.
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

from sugarcode.extra_doc import historical_linguistics as mod

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
    first = {}
    latest = {}
    for word, stage, score in rows:
        if word not in first:
            first[word] = score
        latest[word] = score
    drift = {}
    for word in first:
        drift[word] = latest[word] - first[word]
    risen = sorted(word for word in drift if drift[word] >= 3)
    fallen = sorted(word for word in drift if drift[word] <= -3)
    top = max(abs(v) for v in drift.values())
    supply = list(dict.fromkeys(w for w, _s, _c in rows))
    volatile = next(w for w in supply if abs(drift[w]) == top)
    return {'total': len(rows), 'drift': drift, 'risen': risen,
            'fallen': fallen, 'volatile': volatile}

def battery(m):
    # a volatile tie ignores alphabetical order
    r = m.trace_shifts([('z', 's1', 1), ('z', 's2', 6),
                        ('a', 's1', 1), ('a', 's2', 6)])
    assert r['volatile'] == 'z'

    rng = random.Random(1891)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.trace_shifts(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for word in drift:',
     '    for word in sorted(drift):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
