"""Row 1577, Acoustic Emission Testing.

acoustic_event_fixture multiplies supplied event x count by supplied
background y count plus one. Returns sorted activity, exceeds strict
labels, total and threshold. No acoustic emission testing, defect
detection, physical wave model, real event classification, physical units
or engineering safety judgement is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
threshold defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: acoustic emission testing, defect detection, physical wave model, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied event/background count weighted exceedance, no acoustic emission testing'
NOT_CLAIMED = ('acoustic emission testing', 'defect detection', 'physical wave model', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def acoustic_event_fixture(rows, threshold=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(threshold) is not int or not 0 <= threshold <= 10:
        raise ValueError('threshold must be a nonbool integer between 0 and 10')
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
    values=sorted((n,x*(y+1)) for n,x,y in clean)
    return {'activity':values,'exceeds':[n for n,v in values if v>threshold],
            'total':sum(v for n,v in values),'threshold':threshold}
