"""Row 838, Analogical Reasoning - Reasons by analogy: complete a:b as c:?.

analogy_complete takes pairs, a list or tuple of 1 to 4 (a, b) tuples of
nonbool ints from 0 to 100, and c, a nonbool int from 0 to 100.
Two rules are tried on the pairs. Shift holds when b - a is the same for every
pair, and its answer is c plus that difference. Scale holds when every a is
above 0, a divides b and b // a is the same for every pair, and its answer is
c times that factor.
Returns rule ('shift', 'scale', 'both' or 'none', naming the rules that hold)
and answer (the result of the rule that holds, None when no rule holds, when
the shift answer is negative, or when both rules hold and give different
answers).
Checks, in this order: pairs type, pairs size, each pair (shape, a, b), c.
NOT_CLAIMED: real analogical reasoning, learner insight, relation validity
beyond shift and scale, curriculum fit, production readiness.
"""

SCOPE = 'PARTIAL: completes a supplied pair by a shift or scale rule, no reasoning is performed'
NOT_CLAIMED = ('real analogical reasoning', 'learner insight', 'relation validity beyond shift and scale',
               'curriculum fit', 'production readiness')


def _num(x):
    return type(x) is int and 0 <= x <= 100


def analogy_complete(pairs, c):
    if type(pairs) not in (list, tuple):
        raise TypeError('pairs must be a list or tuple')
    if not 1 <= len(pairs) <= 4:
        raise ValueError('pairs must contain 1 to 4 entries')
    rows = []
    for p in pairs:
        if type(p) not in (list, tuple) or len(p) != 2:
            raise ValueError('each pair must be an (a, b) tuple')
        a, b = p
        if not _num(a):
            raise ValueError('a must be a nonbool integer between 0 and 100')
        if not _num(b):
            raise ValueError('b must be a nonbool integer between 0 and 100')
        rows.append((a, b))
    if not _num(c):
        raise ValueError('c must be a nonbool integer between 0 and 100')
    diffs = {b - a for a, b in rows}
    shift = len(diffs) == 1
    scale = all(a > 0 and b % a == 0 for a, b in rows) and len({b // a for a, b in rows}) == 1
    s_ans = c + diffs.pop() if shift else None
    if s_ans is not None and s_ans < 0:
        s_ans = None
    k_ans = c * (rows[0][1] // rows[0][0]) if scale else None
    if shift and scale:
        return {'rule': 'both', 'answer': s_ans if s_ans == k_ans else None}
    if shift:
        return {'rule': 'shift', 'answer': s_ans}
    if scale:
        return {'rule': 'scale', 'answer': k_ans}
    return {'rule': 'none', 'answer': None}
