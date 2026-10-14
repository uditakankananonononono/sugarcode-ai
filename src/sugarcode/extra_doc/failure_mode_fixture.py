"""Row 1530, Failure Analysis.

failure_mode_fixture multiplies supplied severity x and occurrence y
counts by fixed detectability, ranks descending product and label ascending.
Returns priorities, highest tied labels, total and detectability. This is
abstract count-priority bookkeeping, not failure analysis, root cause
inference, real risk validation, occurrence probability or safety assessment.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
detectability defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, detectability, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: failure analysis, root cause inference, risk validation, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied severity/occurrence count priority rank, no failure analysis'
NOT_CLAIMED = ('failure analysis', 'root cause inference', 'risk validation', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def failure_mode_fixture(rows, detectability=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(detectability) is not int or not 1 <= detectability <= 5:
        raise ValueError('detectability must be a nonbool integer between 1 and 5')
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
    values=sorted(((n,x*y*detectability) for n,x,y in clean),key=lambda r:(-r[1],r[0]))
    return {'priorities':values,'highest':[n for n,v in values if v==values[0][1]],
            'total':sum(v for n,v in values),'detectability':detectability}
