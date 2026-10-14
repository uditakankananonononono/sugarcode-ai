"""Row 1382, Weather Derivatives.

weather_degree_fixture treats supplied abstract temperature count x and
duration count y as weighted deviations below and above base. Returns
sorted degrees (label,heating,cooling), heating/cooling totals and neutral
labels exactly at base regardless of duration. No real weather derivative
valuation, weather forecast, contract interpretation or advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
base defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, base, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: weather derivative valuation, weather forecast, contract interpretation, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: aggregates supplied count temperature deviations, no weather derivative valuation'
NOT_CLAIMED = ('weather derivative valuation', 'weather forecast', 'contract interpretation', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def weather_degree_fixture(rows, base=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(base) is not int or not 0 <= base <= 10:
        raise ValueError('base must be a nonbool integer between 0 and 10')
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
    values=sorted((n,max(base-x,0)*y,max(x-base,0)*y) for n,x,y in clean)
    return {'degrees':values,'heating':sum(h for n,h,c in values),
            'cooling':sum(c for n,h,c in values),'neutral':sorted(n for n,x,y in clean if x==base)}
