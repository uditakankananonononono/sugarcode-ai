"""Row 1396, Impact Investing.

impact_unit_fixture divides supplied benefit count x by cost count y,
undefined at zero cost, and screens ratios meeting minimum. Returns sorted
ratios Fraction strings or None, passing, undefined and total_benefit. No
actual impact investing assessment, impact verification, causality,
investment selection, suitability or financial advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: impact investing assessment, impact verification, investment selection, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied benefit/cost count unit screen, no impact investing assessment'
NOT_CLAIMED = ('impact investing assessment', 'impact verification', 'investment selection', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def impact_unit_fixture(rows, minimum=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 0 <= minimum <= 5:
        raise ValueError('minimum must be a nonbool integer between 0 and 5')
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
    values=sorted((n,F(x,y) if y else None) for n,x,y in clean)
    return {'ratios':[(n,str(v)) if v is not None else (n,None) for n,v in values],
            'passing':[n for n,v in values if v is not None and v>=minimum],
            'undefined':[n for n,v in values if v is None],'total_benefit':sum(x for n,x,y in clean)}
