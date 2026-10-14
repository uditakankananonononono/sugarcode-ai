"""Row 1468, Affect Detection.

affect_count_fixture partitions supplied abstract positive x and negative
y indicator counts using strict signed margin. Returns sorted labels
(label,positive/negative/neutral) and corresponding sorted lists. Equality
at either margin is neutral. No affect detection, emotion inference,
physiological or sensor analysis, psychological claim or diagnosis is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
margin defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, margin, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: affect detection, emotion inference, sensor analysis, production readiness.
"""

SCOPE = 'PARTIAL: supplied positive/negative indicator count partition, no affect detection'
NOT_CLAIMED = ('affect detection', 'emotion inference', 'sensor analysis', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def affect_count_fixture(rows, margin=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(margin) is not int or not 0 <= margin <= 10:
        raise ValueError('margin must be a nonbool integer between 0 and 10')
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
    values=sorted((n,'positive' if x-y>margin else 'negative' if y-x>margin else 'neutral') for n,x,y in clean)
    return {'labels':values,'positive':[n for n,s in values if s=='positive'],
            'negative':[n for n,s in values if s=='negative'],'neutral':[n for n,s in values if s=='neutral']}
