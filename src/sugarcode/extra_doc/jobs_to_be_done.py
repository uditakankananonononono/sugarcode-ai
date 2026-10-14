"""Row 371 Jobs-to-be-Done Analysis - Understands customer motivation: supplied job statements.

Each job is (situation, motivation, outcome), strings of 1 to 80 characters the
caller supplies. Returns the statements "When <situation>, I want to <motivation>,
so I can <outcome>" in input order and motivation counts ranked by count
descending, first appearance on ties. 1 to 24 jobs. Caps are implementation choices.
NOT_CLAIMED: that motivations were discovered or verified, customer interviews,
accuracy of the supplied text, demand, causal claims or product fit.
"""


def analyze_jobs(jobs):
    if type(jobs) not in (list, tuple):
        raise TypeError('jobs must be a list or tuple')
    if not 1 <= len(jobs) <= 24:
        raise ValueError('job count must be between 1 and 24')
    if any(type(j) not in (list, tuple) or len(j) != 3 for j in jobs):
        raise ValueError('jobs must be situation motivation outcome triples')
    if any(type(s) is not str or not 1 <= len(s) <= 80 for j in jobs for s in j):
        raise ValueError('job text must be strings of length 1 through 80')
    tally = {}
    for j in jobs:
        tally[j[1]] = tally.get(j[1], 0) + 1
    order = sorted(tally, key=lambda m: -tally[m])
    return {'statements': ['When %s, I want to %s, so I can %s' % tuple(j) for j in jobs],
            'motivations': [{'motivation': m, 'count': tally[m]} for m in order],
            'motivation_validated': False}
