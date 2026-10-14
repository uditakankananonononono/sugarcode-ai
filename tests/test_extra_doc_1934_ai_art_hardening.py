"""Additive hardening for row 1934, Title: AI Art.

New-file hardening on top of the graded pair test for row 1934.
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

from sugarcode.extra_doc import ai_art as mod

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
    pulls = {}
    counts = {}
    for piece, studio, weight in rows:
        if studio not in pulls:
            pulls[studio] = 0
            counts[studio] = 0
        if counts[studio] % 2 == 0:
            pulls[studio] += weight
        else:
            pulls[studio] -= weight
        counts[studio] += 1
    rising = sorted(s for s in pulls if pulls[s] > 0)
    top = max(pulls.values())
    supply = list(dict.fromkeys(s for _p, s, _w in rows))
    strongest = next(s for s in supply if pulls[s] == top)
    return {'total': len(rows), 'pulls': pulls,
            'rising': rising, 'strongest': strongest}

def battery(m):
    # a strongest tie ignores alphabetical order
    r = m.alternating_pull([('p1', 'z', 5), ('p2', 'a', 5)])
    assert r['strongest'] == 'z'

    with pytest.raises(ValueError) as info:
        m.alternating_pull([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1934)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.alternating_pull(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for studio in pulls:',
     '    for studio in sorted(pulls):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
