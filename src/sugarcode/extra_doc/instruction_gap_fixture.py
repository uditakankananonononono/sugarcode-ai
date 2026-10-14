"""Row 1427, Instructional Design.

instruction_gap_fixture compares supplied practice y count to ratio
times demonstration x count. Returns sorted alignment signed margins,
sufficient nonnegative labels, needed total deficits and excess total
surpluses without cross-row netting. No actual instructional design,
activity generation, pedagogical validation or learning outcome inference.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
ratio defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, ratio, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: instructional design, pedagogical validation, learning outcome inference, production readiness.
"""

SCOPE = 'PARTIAL: supplied practice/demonstration count alignment gaps, no instructional design'
NOT_CLAIMED = ('instructional design', 'pedagogical validation', 'learning outcome inference', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def instruction_gap_fixture(rows, ratio=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(ratio) is not int or not 1 <= ratio <= 5:
        raise ValueError('ratio must be a nonbool integer between 1 and 5')
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
    values=sorted((n,y-ratio*x) for n,x,y in clean)
    return {'alignment':values,'sufficient':[n for n,v in values if v>=0],
            'needed':sum(max(-v,0) for n,v in values),'excess':sum(max(v,0) for n,v in values)}
