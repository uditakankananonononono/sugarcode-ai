"""Row 1141, Physical Therapy Design.

exercise_repetitions adds supplied repetition counts x+y then partitions
into setsize chunks followed by one positive remainder, omitting zero chunks.
Returns sets as sorted (label,chunk_list), totals as sorted (label,sum).
Counts and set size are caller fixtures, not a prescribed exercise intensity
or physical-therapy design. No medical suitability or safety is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
setsize defaults to 5, an exact int from 1 to 10.
Validation order: rows type, rows size, setsize, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: physical therapy, safe exercise, clinical regimen, patient suitability, production readiness.
"""

SCOPE = 'PARTIAL: partitions supplied repetition counts into bounded sets, no physical therapy is designed'
NOT_CLAIMED = ('physical therapy', 'safe exercise', 'clinical regimen', 'patient suitability', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def exercise_repetitions(rows, setsize=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(setsize) is not int or not 1 <= setsize <= 10:
        raise ValueError('setsize must be a nonbool integer between 1 and 10')
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
    sets = []
    totals = []
    for n, first, second in sorted(clean, key=lambda r: r[0]):
        total = first + second
        full, remainder = divmod(total, setsize)
        chunks = [setsize] * full + ([remainder] if remainder else [])
        sets.append((n, chunks))
        totals.append((n, total))
    return {'sets': sets, 'totals': totals}
