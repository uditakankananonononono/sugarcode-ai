"""Row 1378, Quanto Options.

quanto_fixed_fixture converts positive supplied terminal count x minus
strike count y at a fixed integer conversion. Returns sorted converted,
total, zero labels after conversion and conversion. Zero conversion makes
all payoffs zero. No real quanto-option pricing, FX modeling, correlation
adjustment, instrument valuation or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
conversion defaults to 3, an exact int from 0 to 5.
Validation order: rows type, rows size, conversion, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: quanto option pricing, FX modeling, correlation adjustment, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: converts supplied positive count excess at fixed conversion, no quanto-option pricing'
NOT_CLAIMED = ('quanto option pricing', 'FX modeling', 'correlation adjustment', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def quanto_fixed_fixture(rows, conversion=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(conversion) is not int or not 0 <= conversion <= 5:
        raise ValueError('conversion must be a nonbool integer between 0 and 5')
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
    values=sorted((n,max(x-y,0)*conversion) for n,x,y in clean)
    return {'converted':values,'total':sum(v for n,v in values),
            'zero':[n for n,v in values if v==0],'conversion':conversion}
