"""Row 1375, Chooser Options.

chooser_terminal_fixture compares positive supplied x minus strike call
count to positive strike minus y put count, chooses larger, and chooses call
on ties including both zero. Returns sorted choices (label,choice,payoff),
calls labels and total. It uses two supplied counts, not an earlier-time
chooser-option valuation, stochastic process, market price or advice.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
strike defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, strike, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: chooser option valuation, choice-time modeling, stochastic process, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: chooses greater supplied terminal count excess, no chooser-option valuation'
NOT_CLAIMED = ('chooser option valuation', 'choice-time modeling', 'stochastic process', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def chooser_terminal_fixture(rows, strike=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(strike) is not int or not 0 <= strike <= 10:
        raise ValueError('strike must be a nonbool integer between 0 and 10')
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
    values=sorted((n,'call' if max(x-strike,0)>=max(strike-y,0) else 'put',max(x-strike,strike-y,0)) for n,x,y in clean)
    return {'choices':values,'calls':[n for n,c,v in values if c=='call'],'total':sum(v for n,c,v in values)}
