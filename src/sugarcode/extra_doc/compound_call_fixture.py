"""Row 1374, Compound Options.

compound_call_fixture computes inner positive count x minus inner_strike,
then outer positive inner count minus supplied y strike. Returns sorted
payoffs (label,inner,outer), exercised labels with positive outer and
total_outer. No real compound-option valuation, distinct exercise dates,
market simulation, discounting or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
inner_strike defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, inner_strike, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: compound option valuation, exercise-time modeling, market simulation, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: applies supplied outer-strike counts to inner-call excess, no compound-option valuation'
NOT_CLAIMED = ('compound option valuation', 'exercise-time modeling', 'market simulation', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def compound_call_fixture(rows, inner_strike=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(inner_strike) is not int or not 0 <= inner_strike <= 10:
        raise ValueError('inner_strike must be a nonbool integer between 0 and 10')
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
    values=sorted((n,max(x-inner_strike,0),max(max(x-inner_strike,0)-y,0)) for n,x,y in clean)
    return {'payoffs':values,'exercised':[n for n,i,o in values if o>0],
            'total_outer':sum(o for n,i,o in values)}
