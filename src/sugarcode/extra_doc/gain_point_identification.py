"""Row 370 Gain Point Identification - Finds desired outcomes: supplied outcome ranking.

Outcomes are (label, importance, delivery) with ratings the caller supplies, ints
0..100. Opportunity = importance*(100-delivery). Returns outcomes with positive
opportunity ranked by opportunity descending then input index, plus the labels
with zero opportunity. 1 to 32 outcomes, labels unique strings of 1 to 40
characters with no control, format, private-use, surrogate or unassigned characters. Caps are implementation choices.
NOT_CLAIMED: that outcomes were discovered or verified, customer research,
accuracy of ratings, demand, willingness to pay or product fit.
"""
import unicodedata


def _bad(s):
    return any(unicodedata.category(c)[0] == 'C' for c in s)

def rank_gains(outcomes):
    if type(outcomes) not in (list, tuple):
        raise TypeError('outcomes must be a list or tuple')
    if not 1 <= len(outcomes) <= 32:
        raise ValueError('outcome count must be between 1 and 32')
    if any(type(o) not in (list, tuple) or len(o) != 3 for o in outcomes):
        raise ValueError('outcomes must be label importance delivery triples')
    if any(type(o[0]) is not str or not 1 <= len(o[0]) <= 40 or _bad(o[0]) for o in outcomes):
        raise ValueError('labels must be strings of length 1 through 40 without control or unassigned characters')
    if any(type(v) is not int or not 0 <= v <= 100 for o in outcomes for v in o[1:]):
        raise ValueError('ratings must be nonbool integers zero through 100')
    if len({o[0] for o in outcomes}) != len(outcomes):
        raise ValueError('labels must be unique')
    scores = [o[1] * (100 - o[2]) for o in outcomes]
    order = sorted((i for i, s in enumerate(scores) if s > 0), key=lambda i: (-scores[i], i))
    return {'ranked': [{'label': outcomes[i][0], 'opportunity': scores[i]} for i in order],
            'zero_opportunity': [o[0] for o, s in zip(outcomes, scores) if s == 0],
            'outcomes_validated': False}
