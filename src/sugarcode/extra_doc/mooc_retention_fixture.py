"""Row 1454, MOOCs.

mooc_retention_fixture caps supplied completed y at enrolled x per cohort
and counts dropout as remaining. Returns sorted cohorts
(label,completed,dropout), enrolled/completed totals, retention Fraction
string or None at zero enrollment and meets inclusive percent or None.
No MOOC assessment, course delivery, verified completion or learning
 effectiveness is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 30, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: MOOC assessment, course delivery, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied enrollment/completion count retention gaps, no MOOC assessment'
NOT_CLAIMED = ('MOOC assessment', 'course delivery', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def mooc_retention_fixture(rows, percent=30):
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
    values=sorted((n,min(x,y),max(x-y,0)) for n,x,y in clean)
    enrolled=sum(x for n,x,y in clean); completed=sum(c for n,c,d in values)
    return {'cohorts':values,'enrolled':enrolled,'completed':completed,
            'retention':str(F(completed,enrolled)) if enrolled else None,
            'meets':100*completed>=percent*enrolled if enrolled else None}
