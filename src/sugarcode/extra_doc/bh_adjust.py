"""Row 1089, Benjamini-Hochberg - FDR control.

bh_adjust encodes supplied p-values x/(100+y), sorts ascending p then label,
and reports BH adjusted p at rank i as min(1,min(m*p_j/(j+1) for j>=i)).
Returns adjusted as (label,Fraction string) in p-rank order, rejected as
labels with adjusted p at most level percent in that order. It validates
bounded numeric inputs, not p-value calibration or FDR dependence assumptions.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
level defaults to 5, an exact int from 1 to 100.
Validation order: rows type, rows size, level, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: p-value validity, dependence assumptions, actual FDR guarantee, data provenance, production readiness.
"""

SCOPE = 'PARTIAL: computes exact BH step-up adjustments on supplied rational p-values'
NOT_CLAIMED = ('p-value validity', 'dependence assumptions', 'actual FDR guarantee', 'data provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def bh_adjust(rows, level=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(level) is not int or not 1 <= level <= 100:
        raise ValueError('level must be a nonbool integer between 1 and 100')
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
    from fractions import Fraction as F
    ranked = sorted([(n, F(x, 100+y)) for n, x, y in clean], key=lambda r: (r[1], r[0]))
    adjusted = [F(0)] * len(ranked)
    running = F(1)
    for i in range(len(ranked)-1, -1, -1):
        running = min(running, len(ranked) * ranked[i][1] / (i+1))
        adjusted[i] = running
    return {'adjusted': [(ranked[i][0], str(p)) for i, p in enumerate(adjusted)],
            'rejected': [ranked[i][0] for i, p in enumerate(adjusted) if p <= F(level, 100)]}
