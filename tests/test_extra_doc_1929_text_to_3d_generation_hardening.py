"""Additive hardening for row 1929, Title: Text-to-3D Generation.

New-file hardening on top of the graded pair test for row 1929.
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

from sugarcode.extra_doc import text_to_3d_generation as mod

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
    xors = {}
    for asset, engine, steps in rows:
        if engine not in xors:
            xors[engine] = 0
        xors[engine] ^= steps
    balanced = sorted(e for e in xors if xors[e] == 0)
    top = max(xors.values())
    supply = list(dict.fromkeys(e for _a, e, _s in rows))
    sharpest = next(e for e in supply if xors[e] == top)
    return {'total': len(rows), 'xors': xors,
            'balanced': balanced, 'sharpest': sharpest}

def battery(m):
    # a sharpest tie ignores alphabetical order
    r = m.fuse_steps([('a1', 'z', 4), ('a2', 'a', 4)])
    assert r['sharpest'] == 'z'

    with pytest.raises(ValueError) as info:
        m.fuse_steps([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1929)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.fuse_steps(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for engine in xors:',
     '    for engine in sorted(xors):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
