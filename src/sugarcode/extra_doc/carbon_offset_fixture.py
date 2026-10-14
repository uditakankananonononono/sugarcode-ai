"""Row 1401, Carbon Markets.

carbon_offset_fixture subtracts fixed buffer from supplied available
offset count x, floors at zero, and retires at most obligation count y.
Returns sorted offsets (label,available_after_buffer,retired,gap), retired
and gap totals, covered zero-gap labels. No offset verification, actual
carbon-market compliance, registry action, trade or financial advice.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
buffer defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, buffer, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: carbon market compliance, offset verification, trade execution, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: retires supplied offset counts with fixed buffer, no carbon-market compliance'
NOT_CLAIMED = ('carbon market compliance', 'offset verification', 'trade execution', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def carbon_offset_fixture(rows, buffer=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(buffer) is not int or not 0 <= buffer <= 5:
        raise ValueError('buffer must be a nonbool integer between 0 and 5')
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
    values=sorted((n,max(x-buffer,0),min(max(x-buffer,0),y),max(y-max(x-buffer,0),0)) for n,x,y in clean)
    return {'offsets':values,'retired':sum(r for n,a,r,g in values),'gap':sum(g for n,a,r,g in values),
            'covered':[n for n,a,r,g in values if g==0]}
