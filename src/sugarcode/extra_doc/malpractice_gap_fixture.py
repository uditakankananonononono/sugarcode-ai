"""Row 1301, Legal Malpractice.

malpractice_gap_fixture floors abstract planned x minus completed y count at
zero. Returns sorted gaps, above labels strictly beyond tolerance, zero labels
and maximum. No attorney conduct, standard of care, breach, causation, damages
or legal malpractice is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tolerance defaults to 1, an exact int from 0 to 10.
Validation order: rows type, rows size, tolerance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal malpractice, standard of care, causation or damages, legal advice, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied planned/completed count gaps, no malpractice judgment'
NOT_CLAIMED = ('legal malpractice', 'standard of care', 'causation or damages', 'legal advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def malpractice_gap_fixture(rows, tolerance=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tolerance) is not int or not 0 <= tolerance <= 10:
        raise ValueError('tolerance must be a nonbool integer between 0 and 10')
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
    gaps=[(n,max(0,x-y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'gaps':gaps,'above':[n for n,v in gaps if v>tolerance],
            'zero':[n for n,v in gaps if v==0],'maximum':max(v for n,v in gaps)}
