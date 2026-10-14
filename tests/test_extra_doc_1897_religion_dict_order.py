"""Dict-order oracle pins for row 1897, Title: Religion.

Additive pins on top of the graded tests for row 1897: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import religion as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


def _expected(rows):
    totals = {}
    counts = {}
    for tradition, practice, adherents in rows:
        if tradition not in totals:
            totals[tradition] = 0
            counts[tradition] = 0
        totals[tradition] += adherents
        counts[tradition] += 1
    streak_tradition = rows[0][0]
    streak_length = 1
    run_tradition = rows[0][0]
    run_length = 1
    for tradition, practice, adherents in rows[1:]:
        if tradition == run_tradition:
            run_length += 1
        else:
            run_tradition = tradition
            run_length = 1
        if run_length > streak_length:
            streak_tradition = run_tradition
            streak_length = run_length
    widespread = sorted(t for t in counts if counts[t] >= 3)
    top = max(totals.values())
    supply = list(dict.fromkeys(t for t, _p, _a in rows))
    devoted = next(t for t in supply if totals[t] == top)
    return {'total': len(rows), 'totals': totals,
            'streak': {'tradition': streak_tradition, 'length': streak_length},
            'widespread': widespread, 'devoted': devoted}


def _pin_order(rows):
    got = mod.survey_traditions(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71897)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)
