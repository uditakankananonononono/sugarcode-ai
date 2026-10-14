"""Row 867, Convergent Thinking - Narrows to best: staged elimination to one winner.

convergent_pick takes options, a list or tuple of 2 to 8 (name, scores)
tuples, weights, a list or tuple of 3 nonbool ints from 1 to 5, and slack, a
nonbool int from 0 to 5 (default 1). name is a printable ASCII string of 1 to
12 characters (control characters are refused), distinct across options.
scores is a list or tuple of 3 nonbool ints from 0 to 10, one per criterion.
The criteria are taken heaviest weight first, ties by position. In each round
the best score on that criterion among the options still in play is found, and
every option scoring more than slack below it is dropped.
Returns order (the criterion positions in the order they were applied), rounds
(the names still in play after each round, in input order), finalists (the
names left after the last round, in input order), totals (a list of (name,
total) for the finalists, in input order, where total adds weight times score
over the three criteria) and winner (the finalist with the highest total,
ties to the smaller name).
Checks, in this order: slack, weights type, weights size, each weight,
options type, options size, each option (shape, name, scores type, scores
size, each score), distinct names.
NOT_CLAIMED: real convergent thinking, fitness of the criteria, decision
quality, learner judgement, production readiness.
"""

SCOPE = 'PARTIAL: staged elimination of supplied options by supplied weights, no thinking is assessed'
NOT_CLAIMED = ('real convergent thinking', 'fitness of the criteria', 'decision quality',
               'learner judgement', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def convergent_pick(options, weights, slack=1):
    if type(slack) is not int or not 0 <= slack <= 5:
        raise ValueError('slack must be a nonbool integer between 0 and 5')
    if type(weights) not in (list, tuple):
        raise TypeError('weights must be a list or tuple')
    if len(weights) != 3:
        raise ValueError('weights must contain 3 entries')
    for w in weights:
        if type(w) is not int or not 1 <= w <= 5:
            raise ValueError('each weight must be a nonbool integer between 1 and 5')
    if type(options) not in (list, tuple):
        raise TypeError('options must be a list or tuple')
    if not 2 <= len(options) <= 8:
        raise ValueError('options must contain 2 to 8 entries')
    rows = []
    for o in options:
        if type(o) not in (list, tuple) or len(o) != 2:
            raise ValueError('each option must be a (name, scores) tuple')
        name, scores = o
        if not _label(name):
            raise ValueError('each name must be a printable ASCII string of 1 to 12 characters')
        if type(scores) not in (list, tuple):
            raise ValueError('scores must be a list or tuple')
        if len(scores) != 3:
            raise ValueError('scores must contain 3 entries')
        for s in scores:
            if type(s) is not int or not 0 <= s <= 10:
                raise ValueError('each score must be a nonbool integer between 0 and 10')
        rows.append((name, tuple(scores)))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('names must be distinct')
    order = sorted(range(3), key=lambda c: (-weights[c], c))
    alive = rows
    rounds = []
    for c in order:
        best = max(r[1][c] for r in alive)
        alive = [r for r in alive if best - r[1][c] <= slack]
        rounds.append([r[0] for r in alive])
    totals = [(n, sum(w * s for w, s in zip(weights, sc))) for n, sc in alive]
    winner = min(totals, key=lambda t: (-t[1], t[0]))[0]
    return {'order': order, 'rounds': rounds, 'finalists': [r[0] for r in alive],
            'totals': totals, 'winner': winner}
