"""Row 1325, Payback Period.

payback_prefix_fixture orders nonnegative return count x by supplied integer
period y then label. Returns prefixes (label,period,cumulative_count), period
of first cumulative count at least outlay or None, recovered and final shortfall.
Zero outlay pays back at period zero. No within-period interpolation, discounting,
actual cash, risk or financial advice is included.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
outlay defaults to 5, an exact int from 0 to 80.
Validation order: rows type, rows size, outlay, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real investment recovery, discounted payback, cash provenance, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: counts undiscounted supplied count payback prefixes, no investment advice'
NOT_CLAIMED = ('real investment recovery', 'discounted payback', 'cash provenance', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def payback_prefix_fixture(rows, outlay=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(outlay) is not int or not 0 <= outlay <= 80:
        raise ValueError('outlay must be a nonbool integer between 0 and 80')
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
    ordered=sorted(clean,key=lambda r:(r[2],r[0]))
    total=0; prefixes=[]
    period=0 if outlay==0 else None
    for n,x,y in ordered:
        total+=x
        prefixes.append((n,y,total))
        if period is None and total>=outlay: period=y
    return {'prefixes':prefixes,'period':period,'recovered':period is not None,
            'shortfall':max(0,outlay-total)}
