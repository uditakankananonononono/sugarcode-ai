"""Row 1343, Information Ratio.

information_squared_fixture forms active abstract count x minus benchmark
y and reports squared scale times mean divided by population deviation,
plus sign, defined and active_total. Zero active variance yields None.
No actual returns, benchmark validity, tracking error estimate, annualization
or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
scale defaults to 1, an exact int from 1 to 5.
Validation order: rows type, rows size, scale, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real information ratio, benchmark validity, annualization, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: reports squared supplied active-count/deviation ratio, no real information ratio'
NOT_CLAIMED = ('real information ratio', 'benchmark validity', 'annualization', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def information_squared_fixture(rows, scale=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(scale) is not int or not 1 <= scale <= 5:
        raise ValueError('scale must be a nonbool integer between 1 and 5')
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
    count=len(clean); values=[x-y for n,x,y in clean]
    total=sum(values); centered=count*sum(v*v for v in values)-total*total
    squared=F(scale*scale*total*total,centered) if centered else None
    return {'squared':str(squared) if squared is not None else None,
            'sign':(total>0)-(total<0),'defined':centered!=0,'active_total':total}
