"""Row 1303, Legal Aid.

aid_queue_fixture floors abstract requested x minus supplied y count at zero
and ranks unmet descending then label. Returns unmet, above labels strictly
beyond allowance, zero labels and total. No eligibility, means test, priority,
legal aid service or real representation is assessed or arranged.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
allowance defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, allowance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal aid, client eligibility, legal priority, real representation, production readiness.
"""

SCOPE = 'PARTIAL: ranks abstract supplied unmet count tokens, no legal aid eligibility'
NOT_CLAIMED = ('legal aid', 'client eligibility', 'legal priority', 'real representation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def aid_queue_fixture(rows, allowance=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(allowance) is not int or not 0 <= allowance <= 10:
        raise ValueError('allowance must be a nonbool integer between 0 and 10')
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
    unmet=[(n,max(0,x-y)) for n,x,y in clean]
    unmet.sort(key=lambda r:(-r[1],r[0]))
    return {'unmet':unmet,'above':[n for n,v in unmet if v>allowance],
            'zero':[n for n,v in unmet if v==0],'total':sum(v for n,v in unmet)}
