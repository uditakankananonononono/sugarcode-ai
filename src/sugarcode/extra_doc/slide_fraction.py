"""Row 1123, Pathology Slide Analysis.

slide_fraction treats x as caller-counted stained pixels and y as other
pixels in a region. Returns fractions as sorted (label,x/(x+y) Fraction
string), at_least as sorted labels whose fraction is at least minimum percent.
Counts must both be positive. This computes supplied fractions only, not image
analysis, stain identity, pathology interpretation or clinical significance.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 100; bool and all subclasses are refused.
minimum defaults to 50, an exact int from 1 to 100.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: slide interpretation, diagnosis, cell identity, measurement provenance, production readiness.
"""

SCOPE = 'PARTIAL: computes supplied stained-region fractions, no pathology slide is interpreted'
NOT_CLAIMED = ('slide interpretation', 'diagnosis', 'cell identity', 'measurement provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def slide_fraction(rows, minimum=50):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 1 <= minimum <= 100:
        raise ValueError('minimum must be a nonbool integer between 1 and 100')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 1 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 1 and 100')
        if type(y) is not int or not 1 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 1 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    fractions = [(n, F(stained, stained + other)) for n, stained, other in sorted(clean, key=lambda r: r[0])]
    return {'fractions': [(n, str(p)) for n, p in fractions],
            'at_least': [n for n, p in fractions if 100 * p >= minimum]}
