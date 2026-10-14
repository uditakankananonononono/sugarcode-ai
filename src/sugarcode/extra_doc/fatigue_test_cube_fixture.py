"""Row 1562, Fatigue Testing.

fatigue_test_cube_fixture multiplies supplied load x count cubed by
repetition y count and gain. Returns sorted damage_counts, total, zero
labels and gain. No fatigue testing, physical damage prediction, lifetime
estimate, stress validation, physical units or engineering safety
judgement is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 6; bool and all subclasses are refused.
gain defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, gain, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: fatigue testing, damage prediction, lifetime estimate, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied repeated load count cubic budget, no fatigue testing'
NOT_CLAIMED = ('fatigue testing', 'damage prediction', 'lifetime estimate', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def fatigue_test_cube_fixture(rows, gain=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(gain) is not int or not 1 <= gain <= 5:
        raise ValueError('gain must be a nonbool integer between 1 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 6:
            raise ValueError('x must be a nonbool integer between 0 and 6')
        if type(y) is not int or not 0 <= y <= 6:
            raise ValueError('y must be a nonbool integer between 0 and 6')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    values=sorted((n,gain*x*x*x*y) for n,x,y in clean)
    return {'damage_counts':values,'total':sum(v for n,v in values),'zero':[n for n,v in values if v==0],
            'gain':gain}
