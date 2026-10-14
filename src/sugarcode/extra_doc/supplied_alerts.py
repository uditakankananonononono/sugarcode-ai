"""Row 1116, Clinical Decision Support.

supplied_alerts compares supplied integer measure x with caller-written rule
threshold y plus offset. An alert requires x>y+offset, strictly. Returns
alerts as (label,excess) sorted by label, clear as other sorted labels, review
as whether any alert exists. Labels and thresholds have no medical semantics
assigned by this function. This is rule bookkeeping, not clinical care.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
offset defaults to 0, an exact int from 0 to 5.
Validation order: rows type, rows size, offset, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: clinical decision, diagnosis, treatment advice, rule validity, production readiness.
"""

SCOPE = 'PARTIAL: checks supplied integer measures against supplied rule thresholds, no clinical decision is made'
NOT_CLAIMED = ('clinical decision', 'diagnosis', 'treatment advice', 'rule validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def supplied_alerts(rows, offset=0):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(offset) is not int or not 0 <= offset <= 5:
        raise ValueError('offset must be a nonbool integer between 0 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 0 and 100')
        if type(y) is not int or not 0 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 0 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    alerts = [(n, measure - threshold - offset) for n, measure, threshold in sorted(clean, key=lambda r: r[0]) if measure > threshold + offset]
    clear = sorted(n for n, measure, threshold in clean if measure <= threshold + offset)
    return {'alerts': alerts, 'clear': clear, 'review': bool(alerts)}
