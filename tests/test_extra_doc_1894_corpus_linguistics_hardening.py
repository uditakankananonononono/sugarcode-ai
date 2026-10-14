"""Additive hardening for row 1894, Title: Corpus Linguistics.

New-file hardening on top of the graded pair test for row 1894.
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

from sugarcode.extra_doc import corpus_linguistics as mod

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
    totals = {}
    best = {}
    leader = None
    for token, genre, frequency in rows:
        if genre not in totals:
            totals[genre] = 0
        totals[genre] += frequency
        if leader is None and totals[genre] >= 20:
            leader = genre
        if token not in best or frequency > best[token]:
            best[token] = frequency
    frontrunners = sorted(g for g in totals if totals[g] >= 20)
    top = max(best.values())
    supply = list(dict.fromkeys(t for t, _g, _f in rows))
    richest = next(t for t in supply if best[t] == top)
    return {'total': len(rows), 'totals': totals, 'leader': leader,
            'frontrunners': frontrunners, 'richest': richest}

def battery(m):
    # a richest tie ignores alphabetical order
    r = m.analyze_corpus([('z', 'g1', 5), ('a', 'g2', 5)])
    assert r['richest'] == 'z'

    rng = random.Random(1894)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.analyze_corpus(rows) == _expected(rows)
    return True


MUTANTS = [
    ('    for token in best:',
     '    for token in sorted(best):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
