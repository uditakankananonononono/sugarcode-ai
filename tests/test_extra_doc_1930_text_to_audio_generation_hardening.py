"""Additive hardening for row 1930, Title: Text-to-Audio Generation.

New-file hardening on top of the graded pair test for row 1930.
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

from sugarcode.extra_doc import text_to_audio_generation as mod

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
    seen = {}
    supplied = {}
    for track, generator, tone in rows:
        if generator not in seen:
            seen[generator] = set()
            supplied[generator] = 0
        seen[generator].add(tone)
        supplied[generator] += 1
    distinct = {}
    for generator in seen:
        distinct[generator] = len(seen[generator])
    varied = sorted(g for g in distinct if distinct[g] == supplied[g])
    top = max(distinct.values())
    supply = list(dict.fromkeys(g for _t, g, _n in rows))
    richest = next(g for g in supply if distinct[g] == top)
    return {'total': len(rows), 'distinct': distinct,
            'varied': varied, 'richest': richest}

def battery(m):
    # a richest tie ignores alphabetical order
    r = m.distinct_tones([('t1', 'z', 5), ('t2', 'a', 5)])
    assert r['richest'] == 'z'

    with pytest.raises(ValueError) as info:
        m.distinct_tones([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1930)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.distinct_tones(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for generator in distinct:',
     '    for generator in sorted(distinct):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
