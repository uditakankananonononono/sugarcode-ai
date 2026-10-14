"""Row 1346, Hedging Strategies.

hedge_count_fixture subtracts units times supplied abstract offset y from
exposure count x. Returns sorted signed residuals, zero labels, overhedged
negative labels and absolute_total. No instrument, actual exposure, risk,
hedge efficacy, suitable strategy, trade or advice is assessed or executed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
units defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, units, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real hedging strategy, market risk, instrument suitability, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: offsets supplied abstract exposure count tokens, no hedge strategy'
NOT_CLAIMED = ('real hedging strategy', 'market risk', 'instrument suitability', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def hedge_count_fixture(rows, units=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(units) is not int or not 0 <= units <= 5:
        raise ValueError('units must be a nonbool integer between 0 and 5')
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
    residuals=[(n,x-units*y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'residuals':residuals,'zero':[n for n,v in residuals if v==0],
            'overhedged':[n for n,v in residuals if v<0],'absolute_total':sum(abs(v) for n,v in residuals)}
