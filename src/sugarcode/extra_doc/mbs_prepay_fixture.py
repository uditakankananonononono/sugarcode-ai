"""Row 1366, MBS Analysis.

mbs_prepay_fixture applies scheduled principal count to supplied balance x,
caps at balance, then applies supplied prepayment y to the remainder. Returns
sorted payments (label,scheduled_paid,prepaid,remaining), total_paid and
remaining total. No actual mortgage, MBS valuation, interest schedule,
prepayment model, borrower behavior or investment advice is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
scheduled defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, scheduled, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: MBS valuation, prepayment modeling, interest schedule, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: schedules abstract capped prepayment counts, no MBS analysis'
NOT_CLAIMED = ('MBS valuation', 'prepayment modeling', 'interest schedule', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def mbs_prepay_fixture(rows, scheduled=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(scheduled) is not int or not 0 <= scheduled <= 10:
        raise ValueError('scheduled must be a nonbool integer between 0 and 10')
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
    values=sorted((n,min(x,scheduled),min(max(x-scheduled,0),y),max(x-scheduled-y,0)) for n,x,y in clean)
    return {'payments':values,'total_paid':sum(s+p for n,s,p,r in values),
            'remaining':sum(r for n,s,p,r in values)}
