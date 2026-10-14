"""Row 1144, Mental Health Assessment.

assessment_pair_flags takes two supplied integer ratings per caller label.
Returns ranges as sorted (label,low,high), discrepant as sorted labels whose
rating distance strictly exceeds tolerance, spread as largest distance.
No mental health instrument or diagnosis is interpreted. Ratings are supplied
fixtures and no clinical meaning is assigned to their magnitude.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tolerance defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, tolerance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: mental health assessment, diagnosis, clinical instrument validity, rating provenance, production readiness.
"""

SCOPE = 'PARTIAL: reports supplied self-rating disagreement beyond a fixed tolerance, no mental health is assessed'
NOT_CLAIMED = ('mental health assessment', 'diagnosis', 'clinical instrument validity', 'rating provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def assessment_pair_flags(rows, tolerance=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tolerance) is not int or not 0 <= tolerance <= 5:
        raise ValueError('tolerance must be a nonbool integer between 0 and 5')
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
    ranges = [(n, min(first, second), max(first, second)) for n, first, second in sorted(clean, key=lambda r: r[0])]
    discrepant = [n for n, low, high in ranges if high - low > tolerance]
    return {'ranges': ranges, 'discrepant': discrepant,
            'spread': max(high-low for n, low, high in ranges)}
