"""Row 1091, Local FDR - Per-hypothesis FDR.

local_null_odds treats x as positive supplied null density mass and y as
positive supplied alternative mass at each observation. Prior null-to-alt
odds is odds. Bayes local null probability is odds*x/(odds*x+y). Returns
local_fdr as (label,Fraction string) sorted by label, alternative_favored as
sorted labels with local null probability strictly below one half. No density
is estimated and no empirical or frequentist FDR guarantee is made.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 100; bool and all subclasses are refused.
odds defaults to 1, an exact int from 1 to 5.
Validation order: rows type, rows size, odds, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: density calibration, null truth, FDR guarantee, data provenance, production readiness.
"""

SCOPE = 'PARTIAL: computes local null probability from supplied component masses and prior odds'
NOT_CLAIMED = ('density calibration', 'null truth', 'FDR guarantee', 'data provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def local_null_odds(rows, odds=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(odds) is not int or not 1 <= odds <= 5:
        raise ValueError('odds must be a nonbool integer between 1 and 5')
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
    probabilities = [(n, F(odds * null_mass, odds * null_mass + alternative_mass))
                     for n, null_mass, alternative_mass in sorted(clean, key=lambda r: r[0])]
    return {'local_fdr': [(n, str(p)) for n, p in probabilities],
            'alternative_favored': [n for n, p in probabilities if p < F(1, 2)]}
