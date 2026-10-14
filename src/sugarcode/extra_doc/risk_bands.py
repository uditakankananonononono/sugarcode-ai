"""Row 1130, Patient Risk Stratification.

risk_bands adds supplied numeric component scores x+y and assigns floor
(sum/width) as band. Returns bands as sorted (label,band), groups as ascending
band keys mapping to sorted label lists, top as highest occupied band.
These are caller-defined numeric bands, not patient-risk estimates or medical
strata. No thresholds are supplied from clinical guidelines.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
width defaults to 20, an exact int from 1 to 100.
Validation order: rows type, rows size, width, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: patient risk, clinical strata, predictive validity, score provenance, production readiness.
"""

SCOPE = 'PARTIAL: places supplied scores into caller-scaled numeric bands, no patient risk is estimated'
NOT_CLAIMED = ('patient risk', 'clinical strata', 'predictive validity', 'score provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def risk_bands(rows, width=20):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(width) is not int or not 1 <= width <= 100:
        raise ValueError('width must be a nonbool integer between 1 and 100')
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
    bands = [(n, (first + second) // width) for n, first, second in sorted(clean, key=lambda r: r[0])]
    groups = {}
    for n, band in bands:
        groups.setdefault(band, []).append(n)
    return {'bands': bands, 'groups': {k: groups[k] for k in sorted(groups)},
            'top': max(band for n, band in bands)}
