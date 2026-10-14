"""Additive hardening for row 1910, Title: Musicology.

New-file hardening on top of the graded pair test for row 1910.
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

from sugarcode.extra_doc import musicology as mod

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
    seqs = {}
    for piece, composer, tempo in rows:
        if piece not in seqs:
            seqs[piece] = []
        seqs[piece].append(tempo)
    turns = {}
    counts = {}
    for piece in seqs:
        counts[piece] = len(seqs[piece])
        total_turns = 0
        last_dir = 0
        prev = None
        for tempo in seqs[piece]:
            if prev is not None and tempo != prev:
                d = 1 if tempo > prev else -1
                if last_dir != 0 and d != last_dir:
                    total_turns += 1
                last_dir = d
            prev = tempo
        turns[piece] = total_turns
    steady = sorted(p for p in turns if counts[p] >= 2 and turns[p] == 0)
    restless = sorted(p for p in turns if turns[p] >= 2)
    top = max(turns.values())
    supply = list(dict.fromkeys(p for p, _c, _t in rows))
    wildest = next(p for p in supply if turns[p] == top)
    return {'total': len(rows), 'turns': turns, 'steady': steady,
            'restless': restless, 'wildest': wildest}

def battery(m):
    # a wildest tie ignores alphabetical order
    r = m.trace_pieces([('z', 'c1', 5), ('a', 'c2', 5)])
    assert r['wildest'] == 'z'

    with pytest.raises(ValueError) as info:
        m.trace_pieces([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1910)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.trace_pieces(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for piece in turns:',
     '    for piece in sorted(turns):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
