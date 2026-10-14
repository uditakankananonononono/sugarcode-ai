"""Row 1362, Recovery Rates.

recovery_cap_fixture caps each supplied abstract recovered x at face y,
then divides total capped recovery by total face. Returns sorted recovered,
rate Fraction string or None for zero face, meets percent threshold or False
for zero face, and face total. No estimate of future recovery, default forecast,
instrument valuation, actual credit analysis or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 80, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: recovery estimation, default forecast, instrument valuation, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: caps abstract recovered counts at face counts and aggregates, no recovery estimate'
NOT_CLAIMED = ('recovery estimation', 'default forecast', 'instrument valuation', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def recovery_cap_fixture(rows, percent=80):
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
        if type(x) is not int or not 0 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 0 and 10')
        if type(y) is not int or not 0 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 0 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    values=sorted((n,min(x,y)) for n,x,y in clean)
    face=sum(y for n,x,y in clean); recovered=sum(v for n,v in values)
    return {'recovered':values,'rate':str(F(recovered,face)) if face else None,
            'meets':100*recovered>=percent*face if face else False,'face':face}
