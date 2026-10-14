"""Row 1133, Mortality Prediction.

outcome_prior treats x,y as caller-supplied counts of two unspecified outcomes.
Smooth the first fraction using prior counts in each outcome: (x+prior)/
(x+y+2*prior). Returns estimates as sorted (label,Fraction string), above_half
as sorted labels with fraction strictly above one half. Outcomes receive no
medical meaning; no patient mortality probability or model is produced.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
prior defaults to 1, an exact int from 1 to 5.
Validation order: rows type, rows size, prior, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: mortality risk, clinical prediction, population calibration, outcome provenance, production readiness.
"""

SCOPE = 'PARTIAL: smooths supplied binary outcome counts with a symmetric pseudo-count, no mortality risk is predicted'
NOT_CLAIMED = ('mortality risk', 'clinical prediction', 'population calibration', 'outcome provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def outcome_prior(rows, prior=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(prior) is not int or not 1 <= prior <= 5:
        raise ValueError('prior must be a nonbool integer between 1 and 5')
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
    estimates = [(n, F(first + prior, first + second + 2 * prior)) for n, first, second in sorted(clean, key=lambda r: r[0])]
    return {'estimates': [(n, str(p)) for n, p in estimates],
            'above_half': [n for n, p in estimates if p > F(1, 2)]}
