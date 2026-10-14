"""Additive hardening for row 1927, Title: Text-to-Image Generation.

New-file hardening on top of the graded pair test for row 1927.
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

from sugarcode.extra_doc import text_to_image_generation as mod

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

def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def _expected(rows):
    divisors = {}
    for prompt, sampler, steps in rows:
        if sampler not in divisors:
            divisors[sampler] = steps
        else:
            divisors[sampler] = _gcd(divisors[sampler], steps)
    aligned = sorted(s for s in divisors if divisors[s] > 1)
    top = max(divisors.values())
    supply = list(dict.fromkeys(s for _p, s, _t in rows))
    tightest = next(s for s in supply if divisors[s] == top)
    return {'total': len(rows), 'divisors': divisors,
            'aligned': aligned, 'tightest': tightest}

def battery(m):
    # a tightest tie ignores alphabetical order
    r = m.reduce_steps([('p1', 'z', 4), ('p2', 'a', 4)])
    assert r['tightest'] == 'z'

    with pytest.raises(ValueError) as info:
        m.reduce_steps([('', 't', 1), ('', 't', 1)])
    assert str(info.value).startswith('row 1: ')
    rng = random.Random(1927)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        got = m.reduce_steps(rows)
        want = _expected(rows)
        assert got == want
        for key in want:
            if isinstance(want[key], dict):
                assert list(got[key]) == list(want[key])
    return True


MUTANTS = [
    ('    for sampler in divisors:',
     '    for sampler in sorted(divisors):'),
    ('for i, row in enumerate(rows, 1):',
     'for i, row in reversed(list(enumerate(rows, 1))):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
