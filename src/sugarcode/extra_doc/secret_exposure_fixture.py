"""Row 1234, Trade Secret Protection.

secret_exposure_fixture repeatedly subtracts supplied abstract reduction y
from count x, flooring at zero each round. Returns sorted residual, zero
labels and removed counts. No secret content, access permission, secrecy,
security or trade-secret legal status is validated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
rounds defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, rounds, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: trade secret protection, secrecy verification, security guarantee, legal advice, production readiness.
"""

SCOPE = 'PARTIAL: counts supplied abstract exposure reductions, no trade secret protection'
NOT_CLAIMED = ('trade secret protection', 'secrecy verification', 'security guarantee', 'legal advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def secret_exposure_fixture(rows, rounds=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(rounds) is not int or not 0 <= rounds <= 5:
        raise ValueError('rounds must be a nonbool integer between 0 and 5')
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
    residual=[]
    for n,x,y in sorted(clean,key=lambda r:r[0]):
        value=x
        for _ in range(rounds): value=max(0,value-y)
        residual.append((n,value))
    return {'residual':residual,'zero':[n for n,v in residual if v==0],
            'removed':[(n,x-v) for (n,x,y),(m,v) in zip(sorted(clean,key=lambda r:r[0]),residual)]}
