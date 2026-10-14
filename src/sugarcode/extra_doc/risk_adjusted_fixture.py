"""Row 1331, Risk-Adjusted Returns.

risk_adjusted_fixture subtracts baseline from supplied return-count x and
divides by supplied risk-count y. Zero y produces None, not infinity. Returns
sorted ratio Fraction strings/None, undefined labels and defined positive
labels. Counts are abstract; no actual returns/risk, statistical uncertainty,
market data or investment advice is verified or estimated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
baseline defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, baseline, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: actual returns or risk, market data, statistical inference, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: divides supplied excess-return counts by risk counts, no real risk-adjusted return estimate'
NOT_CLAIMED = ('actual returns or risk', 'market data', 'statistical inference', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def risk_adjusted_fixture(rows, baseline=2):
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
    ratios=[(n,F(x-baseline,y) if y else None) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'ratios':[(n,str(v) if v is not None else None) for n,v in ratios],
            'undefined':[n for n,v in ratios if v is None],
            'positive':[n for n,v in ratios if v is not None and v>0]}
