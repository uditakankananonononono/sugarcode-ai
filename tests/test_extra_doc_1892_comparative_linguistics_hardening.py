"""Additive hardening for row 1892, Title: Comparative Linguistics.

New-file hardening on top of the graded pair test for row 1892.
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

from sugarcode.extra_doc import comparative_linguistics as mod

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
    marks = {}
    strength = {}
    for word, language, score in rows:
        if word not in marks:
            marks[word] = {}
            strength[word] = 0
        marks[word][score] = True
        strength[word] += score
    distinct = {}
    for word in marks:
        distinct[word] = len(marks[word])
    uniform = sorted(word for word in distinct if distinct[word] == 1)
    varied = sorted(word for word in distinct if distinct[word] >= 3)
    top = max(strength.values())
    supply = list(dict.fromkeys(w for w, _l, _s in rows))
    firmest = next(w for w in supply if strength[w] == top)
    return {'total': len(rows), 'distinct': distinct, 'uniform': uniform,
            'varied': varied, 'strength': strength, 'firmest': firmest}

def battery(m):
    # a firmest tie ignores alphabetical order
    r = m.match_cognates([('z', 'l1', 5), ('a', 'l2', 5)])
    assert r['firmest'] == 'z'

    rng = random.Random(1892)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.match_cognates(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for word in strength:',
     '    for word in sorted(strength):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
