"""Row 1381, Carbon Trading.

carbon_balance_fixture compares supplied abstract emissions x and
allowance y counts without transferring surpluses between rows. Returns
sorted balances (label,shortfall,surplus), their totals and charge equal
to price times total shortfall. No verified emissions, regulatory compliance,
carbon trading, actual carbon market valuation or investment advice.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
price defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, price, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: carbon trading, regulatory compliance, emissions verification, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: nets supplied emissions/allowance counts and assesses count charge, no carbon trading'
NOT_CLAIMED = ('carbon trading', 'regulatory compliance', 'emissions verification', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def carbon_balance_fixture(rows, price=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(price) is not int or not 0 <= price <= 10:
        raise ValueError('price must be a nonbool integer between 0 and 10')
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
    values=sorted((n,max(x-y,0),max(y-x,0)) for n,x,y in clean)
    return {'balances':values,'shortfall':sum(s for n,s,u in values),
            'surplus':sum(u for n,s,u in values),'charge':price*sum(s for n,s,u in values)}
