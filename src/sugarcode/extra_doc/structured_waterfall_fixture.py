"""Row 1368, Structured Products.

structured_waterfall_fixture pays supplied principal x plus coupon y
caps from funds in label order. Returns waterfall (label,paid,unpaid), left,
full labels with zero unpaid including zero cap, and total_paid. Labels are
fixture priority, not contractual seniority. No real structured-product
valuation, contract interpretation, market risk model or advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
funds defaults to 7, an exact int from 0 to 20.
Validation order: rows type, rows size, funds, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: structured product valuation, contract interpretation, market risk model, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: allocates supplied payment counts down label-ordered caps, no structured-product valuation'
NOT_CLAIMED = ('structured product valuation', 'contract interpretation', 'market risk model', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def structured_waterfall_fixture(rows, funds=7):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(funds) is not int or not 0 <= funds <= 20:
        raise ValueError('funds must be a nonbool integer between 0 and 20')
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
    left=funds; values=[]
    for n,principal,coupon in sorted(clean,key=lambda r:r[0]):
        cap=principal+coupon; paid=min(cap,left); left-=paid
        values.append((n,paid,cap-paid))
    return {'waterfall':values,'left':left,'full':[n for n,p,u in values if u==0],
            'total_paid':funds-left}
