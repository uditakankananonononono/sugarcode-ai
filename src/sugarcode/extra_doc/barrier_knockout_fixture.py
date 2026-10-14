"""Row 1370, Barrier Options.

barrier_knockout_fixture knocks out a supplied abstract two-observation
row whenever x or y meets or exceeds upper barrier. Otherwise its count
payoff is positive y minus x, treating x as fixture strike. Returns sorted
outcomes (label,knocked_out,payoff), knocked_out labels and total_payoff.
No real option valuation, continuous monitoring, stochastic model,
contract interpretation or investment advice is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
barrier defaults to 7, an exact int from 0 to 10.
Validation order: rows type, rows size, barrier, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: barrier option valuation, continuous monitoring, stochastic model, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: knocks out supplied two-point count observations at upper barrier, no option valuation'
NOT_CLAIMED = ('barrier option valuation', 'continuous monitoring', 'stochastic model', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def barrier_knockout_fixture(rows, barrier=7):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(barrier) is not int or not 0 <= barrier <= 10:
        raise ValueError('barrier must be a nonbool integer between 0 and 10')
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
    values=sorted((n,x>=barrier or y>=barrier,max(y-x,0) if x<barrier and y<barrier else 0) for n,x,y in clean)
    return {'outcomes':values,'knocked_out':[n for n,k,p in values if k],
            'total_payoff':sum(p for n,k,p in values)}
