"""Additive hardening for row 1931, Title: Music Generation.

New-file hardening on top of the graded pair test for row 1931.
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

from sugarcode.extra_doc import music_generation as mod

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
    seqs = {}
    for track, composer, level in rows:
        if composer not in seqs:
            seqs[composer] = []
        seqs[composer].append(level)
    variation = {}
    for composer in seqs:
        seq = seqs[composer]
        total = 0
        for k in range(1, len(seq)):
            total += abs(seq[k] - seq[k - 1])
        variation[composer] = total
    flat = sorted(c for c in variation if variation[c] == 0)
    top = max(variation.values())
    supply = list(dict.fromkeys(c for _t, c, _l in rows))
    roughest = next(c for c in supply if variation[c] == top)
    return {'total': len(rows), 'variation': variation,
            'flat': flat, 'roughest': roughest}

def battery(m):
    # a roughest tie ignores alphabetical order
    r = m.track_variation([('t1', 'z', 5), ('t2', 'a', 5)])
    assert r['roughest'] == 'z'

    with pytest.raises(ValueError) as info:
        m.track_variation([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1931)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.track_variation(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for composer in variation:',
     '    for composer in sorted(variation):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
