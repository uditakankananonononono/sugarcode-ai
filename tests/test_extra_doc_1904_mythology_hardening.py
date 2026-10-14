"""Additive hardening for row 1904, Title: Mythology.

New-file hardening on top of the graded pair test for row 1904.
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

from sugarcode.extra_doc import mythology as mod

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
    floors = {}
    for hero, myth, power in rows:
        if hero not in floors:
            floors[hero] = power
        elif power < floors[hero]:
            floors[hero] = power
    unbeaten = sorted(h for h in floors if floors[h] >= 7)
    fragile = sorted(h for h in floors if floors[h] <= 2)
    top = max(floors.values())
    supply = list(dict.fromkeys(h for h, _m, _p in rows))
    sturdiest = next(h for h in supply if floors[h] == top)
    return {'total': len(rows), 'floors': floors, 'unbeaten': unbeaten,
            'fragile': fragile, 'sturdiest': sturdiest}

def battery(m):
    # a sturdiest tie ignores alphabetical order
    r = m.rank_heroes([('z', 'm1', 5), ('a', 'm2', 5)])
    assert r['sturdiest'] == 'z'

    with pytest.raises(ValueError) as info:
        m.rank_heroes([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1904)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.rank_heroes(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for hero in floors:',
     '    for hero in sorted(floors):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
