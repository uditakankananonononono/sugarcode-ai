"""Row 839, Case-Based Reasoning - Uses precedents: nearest cases vote.

case_precedent takes cases, a list or tuple of 1 to 8 (case_id, features,
outcome) tuples, query, a list or tuple of 3 nonbool ints from 0 to 9, and k,
a nonbool int from 1 to 5 (default 3). case_id and outcome are ASCII strings
of 1 to 12 characters, case_id distinct across cases. features is a list or
tuple of 3 nonbool ints from 0 to 9.
The distance of a case is the sum of absolute differences between its features
and the query. The k nearest cases (all of them when fewer than k) are taken in
order of distance, ties by case_id. Their outcomes vote, and the outcome with
the most votes wins. A tie in votes goes to the outcome whose nearest case
comes first in that order.
Returns precedent (the case_id of the nearest case), distance (its distance),
neighbours (the case_ids of the cases that voted, nearest first), outcome (the
winning outcome) and votes (how many neighbours gave it).
Checks, in this order: k, cases type, cases size, each case (shape, case_id,
features type, features size, each feature, outcome), distinct case_ids, query
type, query size, each query value.
NOT_CLAIMED: real case-based reasoning, precedent relevance, legal or clinical
validity, curriculum fit, production readiness.
"""

SCOPE = 'PARTIAL: nearest-case vote over supplied numeric features, no precedent is judged'
NOT_CLAIMED = ('real case-based reasoning', 'precedent relevance', 'legal or clinical validity',
               'curriculum fit', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and 1 <= len(x) <= 12


def case_precedent(cases, query, k=3):
    if type(k) is not int or not 1 <= k <= 5:
        raise ValueError('k must be a nonbool integer between 1 and 5')
    if type(cases) not in (list, tuple):
        raise TypeError('cases must be a list or tuple')
    if not 1 <= len(cases) <= 8:
        raise ValueError('cases must contain 1 to 8 entries')
    rows = []
    for c in cases:
        if type(c) not in (list, tuple) or len(c) != 3:
            raise ValueError('each case must be a (case_id, features, outcome) tuple')
        cid, feats, outcome = c
        if not _label(cid):
            raise ValueError('each case_id must be an ASCII string of 1 to 12 characters')
        if type(feats) not in (list, tuple):
            raise ValueError('features must be a list or tuple')
        if len(feats) != 3:
            raise ValueError('features must contain 3 entries')
        for x in feats:
            if type(x) is not int or not 0 <= x <= 9:
                raise ValueError('each feature must be a nonbool integer between 0 and 9')
        if not _label(outcome):
            raise ValueError('each outcome must be an ASCII string of 1 to 12 characters')
        rows.append((cid, tuple(feats), outcome))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('case_ids must be distinct')
    if type(query) not in (list, tuple):
        raise TypeError('query must be a list or tuple')
    if len(query) != 3:
        raise ValueError('query must contain 3 entries')
    for x in query:
        if type(x) is not int or not 0 <= x <= 9:
            raise ValueError('each query value must be a nonbool integer between 0 and 9')
    ranked = sorted(((sum(abs(a - b) for a, b in zip(f, query)), cid, o) for cid, f, o in rows))
    voters = ranked[:k]
    votes = {}
    for _, _, o in voters:
        votes[o] = votes.get(o, 0) + 1
    top = max(votes.values())
    winner = next(o for _, _, o in voters if votes[o] == top)
    return {'precedent': ranked[0][1], 'distance': ranked[0][0],
            'neighbours': [cid for _, cid, _ in voters], 'outcome': winner, 'votes': top}
