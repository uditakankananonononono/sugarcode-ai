"""Row 1223, Regulatory Compliance.

compliance_count_fixture computes shortfall max(0,required y+extra-completed
x) on abstract supplied counts. Returns label-sorted gaps, covered zero labels,
total_gap and all_covered. No legal requirement is discovered, checked or
certified; caller labels and counts have no regulatory meaning.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
extra defaults to 1, an exact int from 0 to 10.
Validation order: rows type, rows size, extra, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: regulatory compliance, legal obligation discovery, certification, jurisdictional advice, production readiness.
"""

SCOPE = 'PARTIAL: compares supplied abstract completed/required counts, no regulatory compliance judgment'
NOT_CLAIMED = ('regulatory compliance', 'legal obligation discovery', 'certification', 'jurisdictional advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def compliance_count_fixture(rows, extra=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(extra) is not int or not 0 <= extra <= 10:
        raise ValueError('extra must be a nonbool integer between 0 and 10')
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
    gaps=[(n,max(0,y+extra-x)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'gaps':gaps,'covered':[n for n,v in gaps if v==0],
            'total_gap':sum(v for n,v in gaps),'all_covered':all(v==0 for n,v in gaps)}
