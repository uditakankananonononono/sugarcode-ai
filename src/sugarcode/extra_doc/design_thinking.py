"""Row 353 Design Thinking: finite need-coverage selection of prototype ideas (exact).

A human-centered process step on supplied data only: given user needs (ids) and
candidate ideas, each covering some needs at a cost, choose the cheapest set of
ideas that covers every need. Brute force over all idea subsets (at most 10 ideas,
1024 subsets); ties go to fewer ideas, then to the lexicographically smallest
index tuple. Ids are 1 to 40 character strings; cost is a nonbool int or Fraction
(no float) with numerator and denominator at most 32 bits, nonnegative.
At most 8 needs. Caps are implementation choices, not spec values.
Needs, coverage and cost are caller inputs; nothing is inferred from user research.
NOT_CLAIMED: that the needs are real or complete, user research, empathy,
usability, desirability, feasibility or viability of any idea, accessibility
compliance, human testing, ranking of needs, deployment.
"""
from fractions import Fraction
from itertools import combinations

NOT_CLAIMED = ('needs are real or complete', 'user research', 'empathy', 'usability', 'desirability',
               'feasibility or viability', 'accessibility compliance', 'human testing',
               'ranking of needs', 'deployment')


def _id(v):
    if type(v) is not str:
        raise TypeError('ids must be str')
    if not 1 <= len(v) <= 40:
        raise ValueError('ids must be 1 to 40 characters')
    return v


def _cost(v):
    if type(v) not in (int, Fraction):
        raise TypeError('cost must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length() > 32:
            raise ValueError('cost must fit 32 bits')
    elif v.numerator.bit_length() > 32 or v.denominator.bit_length() > 32:
        raise ValueError('cost must fit 32 bits')
    if v < 0:
        raise ValueError('cost must be nonnegative')
    return Fraction(v)


def cover_needs(needs, ideas):
    if type(needs) not in (list, tuple) or type(ideas) not in (list, tuple):
        raise TypeError('needs and ideas must be lists or tuples')
    if not 1 <= len(needs) <= 8:
        raise ValueError('need count must be between 1 and 8')
    if not 1 <= len(ideas) <= 10:
        raise ValueError('idea count must be between 1 and 10')
    need_ids = [_id(n) for n in needs]
    if len(set(need_ids)) != len(need_ids):
        raise ValueError('need ids must be unique')
    parsed = []
    for idea in ideas:
        if type(idea) not in (list, tuple) or len(idea) != 3:
            raise ValueError('each idea must be (id, covered_needs, cost)')
        if type(idea[1]) not in (list, tuple) or len(idea[1]) > 8:
            raise ValueError('covered needs must be a list or tuple of at most 8 ids')
        parsed.append((_id(idea[0]), tuple(_id(c) for c in idea[1]), _cost(idea[2])))
    if len({p[0] for p in parsed}) != len(parsed):
        raise ValueError('idea ids must be unique')
    for p in parsed:
        if any(c not in need_ids for c in p[1]):
            raise ValueError('ideas may only cover listed needs')
    all_needs = set(need_ids)
    best = None
    for size in range(len(parsed) + 1):
        for combo in combinations(range(len(parsed)), size):
            covered = set()
            for i in combo:
                covered.update(parsed[i][1])
            if covered != all_needs:
                continue
            cost = sum((parsed[i][2] for i in combo), Fraction(0))
            key = (cost, size, combo)
            if best is None or key < best:
                best = key
    if best is None:
        raise ValueError('no set of ideas covers every need')
    cost, size, combo = best
    return {'chosen_ideas': [parsed[i][0] for i in combo], 'chosen_indices': list(combo), 'cost': cost,
            'coverage': {n: [parsed[i][0] for i in combo if n in parsed[i][1]] for n in need_ids},
            'user_research_validated': False, 'not_claimed': NOT_CLAIMED}
