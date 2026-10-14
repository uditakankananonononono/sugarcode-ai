"""Row 1205, Health Equity Analysis.

equity_spread_fixture computes each supplied positive ratio x/y and its
max-minus-min spread. Returns label-sorted ratios as Fraction strings,
spread string, wide if spread strictly exceeds percent/100 and lowest
labels at the minimum. No equity, bias, causes or policy remedy is inferred.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
percent defaults to 20, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: health equity determination, population provenance, causal fairness, clinical policy, production readiness.
"""

SCOPE = 'PARTIAL: measures spread of supplied positive coverage ratios, no health equity judgment'
NOT_CLAIMED = ('health equity determination', 'population provenance', 'causal fairness', 'clinical policy', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def equity_spread_fixture(rows, percent=20):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(percent) is not int or not 0 <= percent <= 100:
        raise ValueError('percent must be a nonbool integer between 0 and 100')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    ratios = [(n,F(x,y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    low=min(v for n,v in ratios); high=max(v for n,v in ratios)
    return {'ratios':[(n,str(v)) for n,v in ratios],'spread':str(high-low),
            'wide':100*(high-low)>percent,'lowest':[n for n,v in ratios if v==low]}
