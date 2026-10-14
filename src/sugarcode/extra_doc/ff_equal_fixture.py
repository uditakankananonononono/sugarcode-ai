"""Row 1336, Fama-French.

ff_equal_fixture averages abstract supplied loading x times factor count y
across all rows, then adds baseline. Returns sorted per-row contribution
Fraction strings, total string and nonzero labels. No SMB/HML/market factors,
Fama-French coefficients, returns, estimation or investment advice is provided.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
baseline defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, baseline, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: Fama-French model, factor identification, market estimation, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: averages supplied factor-contribution count pairs, no Fama-French model'
NOT_CLAIMED = ('Fama-French model', 'factor identification', 'market estimation', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ff_equal_fixture(rows, baseline=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(baseline) is not int or not 0 <= baseline <= 10:
        raise ValueError('baseline must be a nonbool integer between 0 and 10')
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
    contributions=[(n,F(x*y,len(clean))) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'contributions':[(n,str(v)) for n,v in contributions],
            'total':str(F(baseline)+sum((v for n,v in contributions),F(0))),
            'nonzero':[n for n,v in contributions if v!=0]}
