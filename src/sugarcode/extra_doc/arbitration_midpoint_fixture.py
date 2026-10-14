"""Row 1282, Arbitration.

arbitration_midpoint_fixture weights abstract first count x by weight and
second y by one, dividing by weight plus one. Returns sorted proposal Fraction
strings, same equal-input labels and total. No actual parties, evidence,
consent, arbitration award, legal ruling or binding agreement is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
weight defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, weight, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: arbitration, award or legal ruling, party consent, binding agreement, production readiness.
"""

SCOPE = 'PARTIAL: computes abstract supplied midpoint proposals, no arbitration'
NOT_CLAIMED = ('arbitration', 'award or legal ruling', 'party consent', 'binding agreement', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def arbitration_midpoint_fixture(rows, weight=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(weight) is not int or not 1 <= weight <= 5:
        raise ValueError('weight must be a nonbool integer between 1 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 0 and 10')
        if type(y) is not int or not 0 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 0 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    proposals=[(n,F(weight*x+y,weight+1)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'proposals':[(n,str(v)) for n,v in proposals],
            'same':sorted(n for n,x,y in clean if x==y),
            'total':str(sum((v for n,v in proposals),F(0)))}
