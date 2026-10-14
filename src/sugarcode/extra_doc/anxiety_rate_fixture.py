"""Row 1146, Anxiety Assessment.

anxiety_rate_fixture divides supplied event count x by supplied positive
exposure count y, allowing x>y. Returns rates as (label,Fraction string)
ranked descending by exact rate then label, above as those strictly above
minimum percent in rank order, overexposure as sorted labels with x>y.
These are abstract event/exposure ratios, not anxiety ratings or medical risk.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
minimum defaults to 50, an exact int from 0 to 100.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: anxiety assessment, clinical instrument, diagnosis, event provenance, production readiness.
"""

SCOPE = 'PARTIAL: ranks supplied event counts relative to supplied exposure counts, no anxiety is assessed'
NOT_CLAIMED = ('anxiety assessment', 'clinical instrument', 'diagnosis', 'event provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def anxiety_rate_fixture(rows, minimum=50):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 0 <= minimum <= 100:
        raise ValueError('minimum must be a nonbool integer between 0 and 100')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    rates = [(n, F(events, exposure)) for n, events, exposure in clean]
    rates.sort(key=lambda r: (-r[1], r[0]))
    return {'rates': [(n, str(r)) for n, r in rates],
            'above': [n for n, r in rates if 100 * r > minimum],
            'overexposure': sorted(n for n, events, exposure in clean if events > exposure)}
