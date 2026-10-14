"""Row 1465, Educational Data Mining.

edm_support_fixture uses supplied event count x and coevent count y,
caps coevents at events and screens support share at percent. Returns sorted
supports Fraction strings or None for zero events, frequent, undefined and
events total. No educational data mining, pattern discovery, event
collection, causal inference or pedagogical recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 50, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: educational data mining, pattern discovery, causal inference, production readiness.
"""

SCOPE = 'PARTIAL: supplied event/coevent count support screen, no educational data mining'
NOT_CLAIMED = ('educational data mining', 'pattern discovery', 'causal inference', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def edm_support_fixture(rows, percent=50):
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
    values=sorted((n,F(min(x,y),x) if x else None) for n,x,y in clean)
    return {'supports':[(n,str(v)) if v is not None else (n,None) for n,v in values],
            'frequent':[n for n,v in values if v is not None and v>=F(percent,100)],
            'undefined':[n for n,v in values if v is None],'events':sum(x for n,x,y in clean)}
