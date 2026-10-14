"""Dict-order oracle pins for row 1892, Title: Comparative Linguistics.

Additive pins on top of the graded tests for row 1892: every
dict-valued field of the result must iterate its keys in
supply order (kills sorted(dict) and set-backed
implementations, which the equality-only battery cannot
distinguish). Depends on the graded module and the graded
test files; removes nothing.
"""
import random

from sugarcode.extra_doc import comparative_linguistics as mod

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')


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


def _pin_order(rows):
    got = mod.match_cognates(rows)
    want = _expected(rows)
    for key in want:
        if isinstance(want[key], dict):
            assert list(got[key]) == list(want[key])


def test_dict_order_fixed_nonalpha_supply():
    _pin_order([('z', 'y', 1), ('m', 'w', 2), ('a', 'v', 3)])


def test_dict_order_randomized():
    rng = random.Random(71892)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        _pin_order(rows)
