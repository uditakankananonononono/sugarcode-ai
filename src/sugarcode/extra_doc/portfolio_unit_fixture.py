"""Row 1332, Portfolio Optimization.

portfolio_unit_fixture enumerates subsets of supplied abstract cost x and
value y counts within budget. Maximizes value, then minimizes cost, then
lexical sorted label tuple; empty subset allowed. Returns selected labels,
value, cost and unused budget. No actual assets, covariance, diversification,
market risk, optimal real portfolio or investment advice is represented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
budget defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, budget, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real portfolio optimization, market risk, diversification model, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: optimizes abstract supplied integer cost/value subsets, no real portfolio advice'
NOT_CLAIMED = ('real portfolio optimization', 'market risk', 'diversification model', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def portfolio_unit_fixture(rows, budget=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(budget) is not int or not 0 <= budget <= 10:
        raise ValueError('budget must be a nonbool integer between 0 and 10')
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
    from itertools import combinations
    choices=[]
    for size in range(len(clean)+1):
        for subset in combinations(clean,size):
            cost=sum(x for n,x,y in subset); value=sum(y for n,x,y in subset)
            if cost<=budget: choices.append((-value,cost,tuple(sorted(n for n,x,y in subset))))
    best=min(choices)
    return {'selected':list(best[2]),'value':-best[0],'cost':best[1],'unused':budget-best[1]}
