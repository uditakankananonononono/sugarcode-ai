"""Additive hardening for row 1919, Title: Subculture Studies.

New-file hardening on top of the graded pair test for row 1919.
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

from sugarcode.extra_doc import subculture_studies as mod

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
    values = {}
    for scene, zine, buzz in rows:
        if scene not in values:
            values[scene] = {}
        values[scene][buzz] = True
    overlap = sorted(b for b in range(1, 10)
                     if sum(1 for s in values if b in values[s]) >= 2)
    signature = {}
    for scene in values:
        signature[scene] = sorted(b for b in values[scene]
                                  if sum(1 for s in values if b in values[s]) == 1)
    top = max(len(signature[s]) for s in signature)
    supply = list(dict.fromkeys(s for s, _z, _b in rows))
    most_signed = next(s for s in supply if len(signature[s]) == top)
    return {'total': len(rows), 'overlap': overlap,
            'signature': signature, 'most_signed': most_signed}

def battery(m):
    # a most_signed tie ignores alphabetical order
    r = m.read_scenes([('z', 'g1', 5), ('a', 'g2', 6)])
    assert r['most_signed'] == 'z'

    with pytest.raises(ValueError) as info:
        m.read_scenes([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1919)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.read_scenes(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for scene in signature:',
     '    for scene in sorted(signature):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
