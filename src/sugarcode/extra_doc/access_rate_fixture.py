"""Row 1304, Access to Justice.

access_rate_fixture divides positive abstract service x by need y counts,
allowing x>y. Returns sorted rate Fraction strings, met percent/100 labels,
minimum and maximum strings. No community, legal rights, actual service,
access quality, population data or causal fairness is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
percent defaults to 50, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: access-to-justice assessment, population provenance, legal rights, causal fairness, production readiness.
"""

SCOPE = 'PARTIAL: compares abstract supplied service/need ratios, no access-to-justice assessment'
NOT_CLAIMED = ('access-to-justice assessment', 'population provenance', 'legal rights', 'causal fairness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def access_rate_fixture(rows, percent=50):
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
    rates=[(n,F(x,y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'rates':[(n,str(v)) for n,v in rates],'met':[n for n,v in rates if 100*v>=percent],
            'minimum':str(min(v for n,v in rates)),'maximum':str(max(v for n,v in rates))}
