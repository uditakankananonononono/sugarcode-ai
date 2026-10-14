"""Row 1085, False Discovery Rate Control - Manage false positives.

false_discovery_budget orders hypotheses by supplied ranking score x,
ascending with label ties. y is supplied posterior null probability percent.
Select the longest prefix whose average y is at most level; later prefixes
may become feasible after earlier ones fail. Returns selected in rank order,
expected_false as sum(y)/100 Fraction string, expected_fraction as average
y/100 Fraction string, zero with no selections. This is posterior expected
false-discovery budgeting, not a verified frequentist FDR controller.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
level defaults to 10, an exact int from 0 to 100.
Validation order: rows type, rows size, level, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: frequentist FDR guarantee, posterior calibration, null truth, data provenance, production readiness.
"""

SCOPE = 'PARTIAL: selects a prefix under supplied posterior-null probability budget, no frequentist FDR is guaranteed'
NOT_CLAIMED = ('frequentist FDR guarantee', 'posterior calibration', 'null truth', 'data provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def false_discovery_budget(rows, level=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(level) is not int or not 0 <= level <= 100:
        raise ValueError('level must be a nonbool integer between 0 and 100')
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
    from fractions import Fraction as F
    ranked = sorted(clean, key=lambda r: (r[1], r[0]))
    selected = []
    null_sum = 0
    for i in range(1, len(ranked) + 1):
        candidate_sum = sum(r[2] for r in ranked[:i])
        if candidate_sum <= level * i:
            selected = [r[0] for r in ranked[:i]]
            null_sum = candidate_sum
    return {'selected': selected, 'expected_false': str(F(null_sum, 100)),
            'expected_fraction': str(F(null_sum, 100 * len(selected))) if selected else '0'}
