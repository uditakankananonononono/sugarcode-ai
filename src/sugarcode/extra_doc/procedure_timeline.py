"""Row 1137, Surgical Planning.

procedure_timeline consumes supplied preparation x and procedure y durations
in caller order. Start at zero and add gap only between rows. Returns timeline
as (label,start,ready,end), ready=start+x and end=ready+y, elapsed as final
end, idle as total between-row gaps. This is abstract duration bookkeeping,
not surgical planning, clinical ordering or an actual schedule.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
gap defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, gap, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: surgical plan, clinical ordering, duration validity, real scheduling, production readiness.
"""

SCOPE = 'PARTIAL: lays out supplied procedure-duration fixtures with fixed gaps, no surgery is planned'
NOT_CLAIMED = ('surgical plan', 'clinical ordering', 'duration validity', 'real scheduling', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def procedure_timeline(rows, gap=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(gap) is not int or not 0 <= gap <= 5:
        raise ValueError('gap must be a nonbool integer between 0 and 5')
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
    timeline = []
    cursor = 0
    for i, (n, preparation, procedure) in enumerate(clean):
        if i:
            cursor += gap
        start = cursor
        ready = start + preparation
        end = ready + procedure
        timeline.append((n, start, ready, end))
        cursor = end
    return {'timeline': timeline, 'elapsed': cursor, 'idle': gap * (len(clean)-1)}
