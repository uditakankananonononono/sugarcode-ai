"""Row 1297, Legal Ethics.

ethics_gap_fixture compares the minimum of abstract paired checklist counts
with required. Returns sorted scores/gaps, zero-gap labels and total_gap.
No professional conduct rule, duty, misconduct or legal ethical conclusion
is interpreted or determined.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
required defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, required, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal ethics, professional rules, misconduct determination, legal advice, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied checklist gaps, no legal ethics assessment'
NOT_CLAIMED = ('legal ethics', 'professional rules', 'misconduct determination', 'legal advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ethics_gap_fixture(rows, required=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(required) is not int or not 0 <= required <= 10:
        raise ValueError('required must be a nonbool integer between 0 and 10')
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
    scores=[(n,min(x,y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    gaps=[(n,max(0,required-v)) for n,v in scores]
    return {'scores':scores,'gaps':gaps,'zero':[n for n,v in gaps if v==0],
            'total_gap':sum(v for n,v in gaps)}
