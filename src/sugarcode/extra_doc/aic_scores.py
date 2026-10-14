"""Row 1110, Information Criteria - AIC, BIC, etc..

aic_scores treats x as supplied integer negative log likelihood and y as
parameter count. Score is 2*x+penalty*y; default penalty two is AIC. Other
penalties are caller-defined, not BIC. Returns scores as (label,score) sorted
ascending score then label, winner as first label, deltas as score minus
minimum in rank order. No likelihood is fitted or criterion validity checked.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
penalty defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, penalty, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: likelihood validity, AIC assumptions, BIC implementation, generalization, production readiness.
"""

SCOPE = 'PARTIAL: computes AIC from supplied negative log likelihood and parameter counts, no model is fitted'
NOT_CLAIMED = ('likelihood validity', 'AIC assumptions', 'BIC implementation', 'generalization', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def aic_scores(rows, penalty=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(penalty) is not int or not 1 <= penalty <= 5:
        raise ValueError('penalty must be a nonbool integer between 1 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 0 and 100')
        if type(y) is not int or not 0 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 0 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    scores = [(n, 2 * negative_log + penalty * parameters) for n, negative_log, parameters in clean]
    scores.sort(key=lambda r: (r[1], r[0]))
    minimum = scores[0][1]
    return {'scores': scores, 'winner': scores[0][0],
            'deltas': [(n, score - minimum) for n, score in scores]}
