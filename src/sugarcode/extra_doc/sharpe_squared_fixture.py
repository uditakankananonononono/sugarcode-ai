"""Row 1341, Sharpe Ratio.

sharpe_squared_fixture forms abstract excess counts x minus y minus baseline per row.
Uses population standard deviation convention and returns squared ratio of
mean excess to that deviation as exact Fraction string, plus sign (-1/0/1),
defined and count. Zero variance yields None. No square-root/annualization,
actual return data, estimated risk or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
baseline defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, baseline, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real Sharpe estimate, annualization, market data, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: reports exact squared Sharpe-count fixture and sign, no real Sharpe estimate'
NOT_CLAIMED = ('real Sharpe estimate', 'annualization', 'market data', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def sharpe_squared_fixture(rows, baseline=2):
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
    count=len(clean); total=sum(x-y-baseline for n,x,y in clean)
    squares=sum((x-y-baseline)**2 for n,x,y in clean)
    centered=count*squares-total*total
    squared=F(total*total,centered) if centered else None
    return {'squared':str(squared) if squared is not None else None,
            'sign':(total>0)-(total<0),'defined':centered!=0,'count':count}
