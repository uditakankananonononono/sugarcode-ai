"""Row 1151, Neuropsychological Testing.

rank_gap_fixture ranks each supplied score column descending with label
ties ascending, then computes second_index-first_index for each label.
Returns differences sorted by label and flagged labels with absolute gap
at least gap. Zero-based ranks are abstract, not test norms or clinical scores.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
gap defaults to 1, an exact int from 0 to 7.
Validation order: rows type, rows size, gap, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: neuropsychological testing, norms, diagnosis, clinical interpretation, production readiness.
"""

SCOPE = 'PARTIAL: contrasts ranks of supplied score columns, no neuropsychological testing'
NOT_CLAIMED = ('neuropsychological testing', 'norms', 'diagnosis', 'clinical interpretation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def rank_gap_fixture(rows, gap=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(gap) is not int or not 0 <= gap <= 7:
        raise ValueError('gap must be a nonbool integer between 0 and 7')
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
    first = sorted(clean, key=lambda r:(-r[1],r[0]))
    second = sorted(clean, key=lambda r:(-r[2],r[0]))
    a = [r[0] for r in first]; b = [r[0] for r in second]
    differences = [(name, b.index(name) - a.index(name)) for name in sorted(a)]
    return {'differences': differences, 'flagged': [n for n,d in differences if abs(d) >= gap]}
