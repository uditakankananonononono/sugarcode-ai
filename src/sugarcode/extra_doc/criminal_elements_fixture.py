"""Row 1264, Criminal Law.

criminal_elements_fixture takes the minimum of abstract supplied checklist
pair counts. Returns sorted floors, met labels at least minimum, nonnegative
gap and zero labels. No offense, elements, mental state, guilt, liability or
criminal law conclusion is evaluated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: criminal law, offense elements, guilt or liability, legal advice, production readiness.
"""

SCOPE = 'PARTIAL: gates abstract supplied checklist pairs, no criminal law analysis'
NOT_CLAIMED = ('criminal law', 'offense elements', 'guilt or liability', 'legal advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def criminal_elements_fixture(rows, minimum=3):
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
    floors=[(n,min(x,y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'floors':floors,'met':[n for n,v in floors if v>=minimum],
            'gap':[(n,max(0,minimum-v)) for n,v in floors],
            'zero':[n for n,v in floors if v==0]}
