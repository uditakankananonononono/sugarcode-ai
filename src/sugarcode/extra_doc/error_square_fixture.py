"""Row 1149, Cognitive Assessment.

error_square_fixture computes squared x-y mismatch for supplied pairs.
Returns errors sorted by label, within labels with squared error<=limit,
worst as maximum squared error and ties as all labels attaining it in label
order. No cognitive scoring, clinical norms or assessment is performed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
limit defaults to 9, an exact int from 0 to 100.
Validation order: rows type, rows size, limit, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: cognitive assessment, clinical instrument, diagnosis, normative comparison, production readiness.
"""

SCOPE = 'PARTIAL: measures squared mismatch of supplied numeric pairs, no cognitive assessment'
NOT_CLAIMED = ('cognitive assessment', 'clinical instrument', 'diagnosis', 'normative comparison', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def error_square_fixture(rows, limit=9):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(limit) is not int or not 0 <= limit <= 100:
        raise ValueError('limit must be a nonbool integer between 0 and 100')
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
    errors = [(n, (x - y) ** 2) for n, x, y in sorted(clean, key=lambda r:r[0])]
    worst = max(v for n, v in errors)
    return {'errors': errors, 'within': [n for n,v in errors if v <= limit],
            'worst': worst, 'ties': [n for n,v in errors if v == worst]}
