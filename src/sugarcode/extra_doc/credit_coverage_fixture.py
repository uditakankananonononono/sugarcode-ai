"""Row 1360, Credit Analysis.

credit_coverage_fixture uses abstract cash x and debt y counts to compute
x minus multiple times y. Returns sorted margins, covered for nonnegative
margins, short for negative margins and total_margin. Zero debt with zero
cash is covered by convention. No creditworthiness, lending decision,
credit rating, financial suitability or investment advice is provided.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
multiple defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, multiple, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: creditworthiness, lending decision, credit rating, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: partitions supplied cash/debt counts by exact coverage multiple, no creditworthiness'
NOT_CLAIMED = ('creditworthiness', 'lending decision', 'credit rating', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def credit_coverage_fixture(rows, multiple=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(multiple) is not int or not 1 <= multiple <= 5:
        raise ValueError('multiple must be a nonbool integer between 1 and 5')
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
    values=sorted((n,x-multiple*y) for n,x,y in clean)
    return {'margins':values,'covered':[n for n,v in values if v>=0],
            'short':[n for n,v in values if v<0],'total_margin':sum(v for n,v in values)}
