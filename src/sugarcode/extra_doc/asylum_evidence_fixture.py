"""Row 1246, Asylum Cases.

asylum_evidence_fixture subtracts supplied abstract conflict y from support
x and orders descending then label. Returns balances, at_least labels
meeting minimum, negative and zero labels. No person's credibility, country
conditions, persecution, legal eligibility or asylum case is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: asylum eligibility, credibility finding, country conditions, legal advice, production readiness.
"""

SCOPE = 'PARTIAL: ranks abstract supplied evidence balances, no asylum case analysis'
NOT_CLAIMED = ('asylum eligibility', 'credibility finding', 'country conditions', 'legal advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def asylum_evidence_fixture(rows, minimum=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 0 <= minimum <= 10:
        raise ValueError('minimum must be a nonbool integer between 0 and 10')
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
    balances=[(n,x-y) for n,x,y in clean]
    balances.sort(key=lambda r:(-r[1],r[0]))
    return {'balances':balances,'at_least':[n for n,v in balances if v>=minimum],
            'negative':[n for n,v in balances if v<0],'zero':[n for n,v in balances if v==0]}
