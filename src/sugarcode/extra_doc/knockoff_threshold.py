"""Row 1093, Knockoffs - Controlled variable selection.

knockoff_threshold forms W=x-y from supplied original/knockoff importance
scores. Choose the smallest positive observed |W| threshold t such that
(1+count(W<=-t))/max(1,count(W>=t)) <= level/100. If none, threshold is None
and no selection. Returns statistics as (label,W) sorted by label, threshold
as integer or None, selected as sorted labels with W>=threshold. Only the
knockoff-plus threshold rule is implemented, not valid knockoff generation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
level defaults to 20, an exact int from 1 to 100.
Validation order: rows type, rows size, level, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: knockoff validity, exchangeability, FDR guarantee, feature generation, production readiness.
"""

SCOPE = 'PARTIAL: applies knockoff-plus threshold to supplied original-minus-knockoff scores'
NOT_CLAIMED = ('knockoff validity', 'exchangeability', 'FDR guarantee', 'feature generation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def knockoff_threshold(rows, level=20):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(level) is not int or not 1 <= level <= 100:
        raise ValueError('level must be a nonbool integer between 1 and 100')
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
    statistics = sorted([(n, x - y) for n, x, y in clean])
    candidates = sorted({abs(w) for n, w in statistics if w != 0})
    threshold = None
    for t in candidates:
        negative = sum(w <= -t for n, w in statistics)
        positive = sum(w >= t for n, w in statistics)
        if 100 * (1 + negative) <= level * max(1, positive):
            threshold = t
            break
    selected = [n for n, w in statistics if threshold is not None and w >= threshold]
    return {'statistics': statistics, 'threshold': threshold, 'selected': selected}
