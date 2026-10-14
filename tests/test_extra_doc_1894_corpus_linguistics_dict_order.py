"""Dict-order oracle pins for row 1894, Title: Corpus Linguistics.

Additive pins on top of the graded tests for row 1894: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import corpus_linguistics as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


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


def _pin_order(rows):
    got = mod.analyze_corpus(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71894)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)
