"""Row171 Regression Discontinuity: PARTIAL triangular local-linear sharp cutoff.

rows exact list1..8 of exact (running, outcome) tuples, exact ints-5..5.
cutoff exact int-5..5, bandwidth exact int1..5. Center x=running-cutoff.
Keep abs(x)<bandwidth, weight=bandwidth-abs(x); left x<0, right x>=0.
Fit a separate weighted intercept+slope on each side. Return side fit as
(intercept,slope) exact Fraction tuple or None when weighted design singular.
Jump=right intercept-left intercept iff both identified. Used IDs in input
order, including duplicates as separate equally reliable observations.
Validation: cutoff, bandwidth, outer rows, each shape then running then outcome.
No continuity/manipulation/design assumptions, valid bandwidth or causality.
"""
from fractions import Fraction as F
SCOPE = 'PARTIAL: exact triangular-kernel local-linear sharp-cutoff discontinuity'
NOT_CLAIMED = ('causal identification', 'continuity assumptions', 'bandwidth selection',
               'manipulation diagnosis', 'sampling uncertainty')


def estimate(cutoff, bandwidth, rows):
    if type(cutoff) is not int or not -5 <= cutoff <= 5:
        raise ValueError('cutoff must be exact int-5..5')
    if type(bandwidth) is not int or not 1 <= bandwidth <= 5:
        raise ValueError('bandwidth must be exact int1..5')
    if type(rows) is not list or not 1 <= len(rows) <= 8:
        raise ValueError('rows must be exact list1..8')
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError('row must be exact running outcome pair tuple')
        if type(row[0]) is not int or not -5 <= row[0] <= 5:
            raise ValueError('running must be exact int-5..5')
        if type(row[1]) is not int or not -5 <= row[1] <= 5:
            raise ValueError('outcome must be exact int-5..5')
    sides = [[], []]
    for i, (running, outcome) in enumerate(rows):
        x = running - cutoff
        if abs(x) < bandwidth:
            sides[int(x >= 0)].append((i, x, outcome, bandwidth-abs(x)))
    fits = []
    for side in sides:
        sw = sum(w for i,x,y,w in side)
        sx = sum(w*x for i,x,y,w in side)
        sy = sum(w*y for i,x,y,w in side)
        sxx = sum(w*x*x for i,x,y,w in side)
        sxy = sum(w*x*y for i,x,y,w in side)
        det = sw*sxx-sx*sx
        fits.append((F(sxx*sy-sx*sxy, det), F(sw*sxy-sx*sy, det)) if det else None)
    return {'left': fits[0], 'right': fits[1],
            'jump': fits[1][0]-fits[0][0] if all(f is not None for f in fits) else None,
            'used': [tuple(i for i,x,y,w in side) for side in sides],
            'causality_identified': False}
