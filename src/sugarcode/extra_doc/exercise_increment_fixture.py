"""Row 1196, Exercise Prescription.

exercise_increment_fixture adds increment to abstract current x and clips
to caller cap y, allowing y below x. Returns sorted counts (label,new_count,
signed_change), at_cap labels whose new count equals cap and decreased
negative-change labels. Values are opaque fixtures. No activity, repetitions,
physical suitability, exercise dose, injury risk or safe program is prescribed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
increment defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, increment, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: exercise prescription, physical suitability, injury or safety, clinical advice, production readiness.
"""

SCOPE = 'PARTIAL: computes capped abstract repetition increments, no exercise prescription'
NOT_CLAIMED = ('exercise prescription', 'physical suitability', 'injury or safety', 'clinical advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def exercise_increment_fixture(rows, increment=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(increment) is not int or not 0 <= increment <= 10:
        raise ValueError('increment must be a nonbool integer between 0 and 10')
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
    counts=[]
    for n,current,cap in sorted(clean,key=lambda r:r[0]):
        new=min(cap,current+increment)
        counts.append((n,new,new-current))
    return {'counts':counts,'at_cap':[n for n,new,change in counts if new==next(y for m,x,y in clean if m==n)],
            'decreased':[n for n,new,change in counts if change<0]}
