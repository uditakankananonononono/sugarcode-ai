"""Row 1263, Energy Law.

energy_balance_fixture subtracts loss from supplied abstract production x,
floors at zero then subtracts demand y. Returns sorted net, positive deficit
for negative balances, balanced zero labels and total. No actual energy,
regulatory compliance, legal rights or contract terms are interpreted.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
loss defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, loss, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: energy law, real energy units, legal compliance, contract interpretation, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied energy balances, no energy law analysis'
NOT_CLAIMED = ('energy law', 'real energy units', 'legal compliance', 'contract interpretation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def energy_balance_fixture(rows, loss=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(loss) is not int or not 0 <= loss <= 10:
        raise ValueError('loss must be a nonbool integer between 0 and 10')
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
    net=[(n,max(0,x-loss)-y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'net':net,'deficit':[(n,-v) for n,v in net if v<0],
            'balanced':[n for n,v in net if v==0],'total':sum(v for n,v in net)}
