"""Row 1225, Due Diligence.

diligence_fraction_fixture divides supplied positive completed x by required
y, allowing x greater than y. Returns label-sorted coverage Fraction strings,
passed labels at least percent/100, unpassed below and all_passed. No document
is read or verified and no legal/transaction readiness is certified.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
percent defaults to 75, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal due diligence, verification of documents, transaction readiness, legal advice, production readiness.
"""

SCOPE = 'PARTIAL: pools supplied positive document tallies, no legal due diligence'
NOT_CLAIMED = ('legal due diligence', 'verification of documents', 'transaction readiness', 'legal advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def diligence_fraction_fixture(rows, percent=75):
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
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    coverage=[(n,F(x,y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    passed=[n for n,v in coverage if 100*v>=percent]
    return {'coverage':[(n,str(v)) for n,v in coverage],'passed':passed,
            'unpassed':[n for n,v in coverage if 100*v<percent],'all_passed':len(passed)==len(clean)}
