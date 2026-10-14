"""Row 1253, Wills and Trusts.

trust_release_fixture computes percent of abstract units x, capped by supplied
y. Returns sorted released Fraction strings, zero labels and total string.
No trust clause, will, beneficiary, legal validity or real asset transfer is
interpreted or created.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 50, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: will or trust drafting, legal validity, beneficiary rights, asset transfer, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied release portions, no will or trust analysis'
NOT_CLAIMED = ('will or trust drafting', 'legal validity', 'beneficiary rights', 'asset transfer', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def trust_release_fixture(rows, percent=50):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(percent) is not int or not 0 <= percent <= 100:
        raise ValueError('percent must be a nonbool integer between 0 and 100')
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
    from fractions import Fraction as F
    released=[(n,min(F(x*percent,100),F(y))) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'released':[(n,str(v)) for n,v in released],
            'zero':[n for n,v in released if v==0],'total':str(sum((v for n,v in released),F(0)))}
