"""Row 1139, Post-Operative Care.

care_checklist_gap uses supplied planned task count x and done count y.
Returns deficits as sorted (label,max(0,x-y)), pending as sorted labels with
deficit strictly above allowance, surplus as labels with done>planned, total
as summed deficits. Tasks have no inferred clinical role, and this inventory
does not direct post-operative care or judge patient safety.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
allowance defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, allowance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: post-operative care, clinical safety, task suitability, completion provenance, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied task counts and completion deficits, no post-operative care is directed'
NOT_CLAIMED = ('post-operative care', 'clinical safety', 'task suitability', 'completion provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def care_checklist_gap(rows, allowance=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(allowance) is not int or not 0 <= allowance <= 5:
        raise ValueError('allowance must be a nonbool integer between 0 and 5')
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
    deficits = [(n, max(0, planned - done)) for n, planned, done in sorted(clean, key=lambda r: r[0])]
    pending = [n for n, d in deficits if d > allowance]
    surplus = sorted(n for n, planned, done in clean if done > planned)
    return {'deficits': deficits, 'pending': pending, 'surplus': surplus, 'total': sum(d for n, d in deficits)}
