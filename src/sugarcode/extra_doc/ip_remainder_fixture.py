"""Row 1229, Intellectual Property.

ip_remainder_fixture floors abstract supplied asset count x minus supplied
coverage count y at zero. Returns residual label/count pairs, over labels
strictly above allowance, covered zero labels and excess labels with y greater than x.
No IP right, ownership, protection or infringement conclusion is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
allowance defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, allowance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: intellectual property rights, ownership verification, infringement analysis, legal advice, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied protected/unprotected counts, no IP analysis'
NOT_CLAIMED = ('intellectual property rights', 'ownership verification', 'infringement analysis', 'legal advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ip_remainder_fixture(rows, allowance=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(allowance) is not int or not 0 <= allowance <= 10:
        raise ValueError('allowance must be a nonbool integer between 0 and 10')
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
    residual=[(n,max(0,x-y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'residual':residual,'over':[n for n,v in residual if v>allowance],
            'covered':[n for n,v in residual if v==0],'excess':sorted(n for n,x,y in clean if y>x)}
