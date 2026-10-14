"""Row 1131, Readmission Prediction.

readmission_fixture applies caller-defined score min(100,coefficient*x+y)
to supplied counts. Returns scores sorted by label, ranking as descending
score labels with label ties, capped as sorted labels whose raw score reaches
or exceeds 100. The score is not a probability or a fitted readmission model;
no medical use or clinical calibration is claimed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
coefficient defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, coefficient, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: readmission probability, clinical prediction, score calibration, data provenance, production readiness.
"""

SCOPE = 'PARTIAL: applies a caller-defined capped count score, no readmission probability is estimated'
NOT_CLAIMED = ('readmission probability', 'clinical prediction', 'score calibration', 'data provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def readmission_fixture(rows, coefficient=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(coefficient) is not int or not 1 <= coefficient <= 5:
        raise ValueError('coefficient must be a nonbool integer between 1 and 5')
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
    scores = [(n, min(100, coefficient * prior + recent)) for n, prior, recent in sorted(clean, key=lambda r: r[0])]
    ranking = sorted(scores, key=lambda r: (-r[1], r[0]))
    return {'scores': scores, 'ranking': [n for n, score in ranking],
            'capped': [n for n, prior, recent in sorted(clean, key=lambda r: r[0]) if coefficient * prior + recent >= 100]}
