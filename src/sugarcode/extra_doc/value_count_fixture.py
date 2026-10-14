"""Row 1413, Value.

value_count_fixture ranks abstract supplied book count x divided by
price count y, descending ratio and label ascending on ties, excluding zero
price. Returns ranked Fraction strings, passing ratios meeting minimum in
rank order and undefined labels sorted. No security valuation, investment
value assessment, real market data, forecast or financial advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: investment value assessment, security valuation, market forecast, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: ranks supplied book/price count ratios, no investment value assessment'
NOT_CLAIMED = ('investment value assessment', 'security valuation', 'market forecast', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def value_count_fixture(rows, minimum=2):
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
    valid=[(n,F(x,y)) for n,x,y in clean if y]
    valid.sort(key=lambda r:(-r[1],r[0]))
    return {'ranked':[(n,str(v)) for n,v in valid],'passing':[n for n,v in valid if v>=minimum],
            'undefined':sorted(n for n,x,y in clean if not y)}
