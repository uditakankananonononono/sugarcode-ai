"""Row 1484, Self-Assessment.

selfrating_gap_fixture subtracts supplied criterion count y from self
rating count x and partitions by tolerance. Returns sorted differences,
aligned inclusive absolute tolerance, self_higher and self_lower strict
outer bands. No self-assessment validity, criterion truth, metacognitive
diagnosis, learner evaluation or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tolerance defaults to 1, an exact int from 0 to 10.
Validation order: rows type, rows size, tolerance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: self assessment validity, metacognitive diagnosis, learner evaluation, production readiness.
"""

SCOPE = 'PARTIAL: supplied self/criterion count signed differences, no self-assessment validity'
NOT_CLAIMED = ('self assessment validity', 'metacognitive diagnosis', 'learner evaluation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def selfrating_gap_fixture(rows, tolerance=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tolerance) is not int or not 0 <= tolerance <= 10:
        raise ValueError('tolerance must be a nonbool integer between 0 and 10')
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
    values=sorted((n,x-y) for n,x,y in clean)
    return {'differences':values,'aligned':[n for n,v in values if abs(v)<=tolerance],
            'self_higher':[n for n,v in values if v>tolerance],
            'self_lower':[n for n,v in values if v<-tolerance]}
