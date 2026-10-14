"""Row 1122, Radiology Report Generation.

radiology_inventory formats only caller-supplied integer observations x and
reference y as exact values scaled by 10**precision. Returns inventory as
(label,observed_Fraction_string,reference_Fraction_string) sorted by label,
above_reference as sorted labels with x>y, scale as 10**precision. This is
an observation inventory, not a radiology report or interpretation; reference
values have no inferred clinical meaning.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
precision defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, precision, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: radiology interpretation, medical report, diagnosis, measurement validity, production readiness.
"""

SCOPE = 'PARTIAL: renders an inventory of supplied integer observations and reference values, no radiology report is authored'
NOT_CLAIMED = ('radiology interpretation', 'medical report', 'diagnosis', 'measurement validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def radiology_inventory(rows, precision=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(precision) is not int or not 0 <= precision <= 5:
        raise ValueError('precision must be a nonbool integer between 0 and 5')
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
    lines = []
    excess = []
    for n, observed, reference in sorted(clean, key=lambda r: r[0]):
        difference = observed - reference
        lines.append((n, str(F(observed, 10 ** precision)), str(F(reference, 10 ** precision))))
        if difference > 0:
            excess.append(n)
    return {'inventory': lines, 'above_reference': excess, 'scale': 10 ** precision}
