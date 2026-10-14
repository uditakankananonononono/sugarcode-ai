"""Additive hardening for row 1898, Title: Theology.

New-file hardening on top of the graded pair test for row 1898.
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

from sugarcode.extra_doc import theology as mod

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
    last = {}
    for doctrine, school, weight in rows:
        if doctrine not in first:
            first[doctrine] = weight
        last[doctrine] = weight
    drifts = {}
    for doctrine in first:
        drifts[doctrine] = last[doctrine] - first[doctrine]
    hardened = sorted(d for d in drifts if drifts[d] >= 3)
    softened = sorted(d for d in drifts if drifts[d] <= -3)
    top = max(abs(v) for v in drifts.values())
    supply = list(dict.fromkeys(d for d, _s, _w in rows))
    volatile = next(d for d in supply if abs(drifts[d]) == top)
    return {'total': len(rows), 'drifts': drifts, 'hardened': hardened,
            'softened': softened, 'volatile': volatile}

def battery(m):
    # a volatile tie ignores alphabetical order
    r = m.weigh_doctrines([('z', 's1', 1), ('z', 's2', 6),
                           ('a', 's1', 1), ('a', 's2', 6)])
    assert r['volatile'] == 'z'

    rng = random.Random(1898)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.weigh_doctrines(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for doctrine in drifts:',
     '    for doctrine in sorted(drifts):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
