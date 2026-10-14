"""Additive hardening for row 1912, Title: Film Studies.

New-file hardening on top of the graded pair test for row 1912.
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

from sugarcode.extra_doc import film_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m

def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message

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
    bests = {}
    counts = {}
    for scene, reel, score in rows:
        if scene not in bests:
            firsts[scene] = score
            bests[scene] = score
            counts[scene] = 0
        if score > bests[scene]:
            bests[scene] = score
        counts[scene] += 1
    natural = sorted(s for s in bests if firsts[s] == bests[s])
    climb = {s: bests[s] - firsts[s] for s in bests if counts[s] >= 2}
    if climb:
        top = max(climb.values())
        supply = list(dict.fromkeys(s for s, _r, _c in rows))
        climber = next(s for s in supply if s in climb and climb[s] == top)
    else:
        climber = None
    return {'total': len(rows), 'bests': bests,
            'natural': natural, 'climber': climber}

def battery(m):
    # a climber tie ignores alphabetical order
    r = m.screen_takes([('z', 'r1', 1), ('z', 'r2', 6),
                        ('a', 'r3', 2), ('a', 'r4', 7)])
    assert r['climber'] == 'z'

    with pytest.raises(ValueError) as info:
        m.screen_takes([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1912)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.screen_takes(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    climber = None\n    for scene in bests:',
     '    climber = None\n    for scene in sorted(bests):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
