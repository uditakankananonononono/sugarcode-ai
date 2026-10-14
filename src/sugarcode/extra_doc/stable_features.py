"""Row 1094, Stability Selection - Stable variable selection.

stable_features treats x,y as inclusion counts from two supplied batches,
each of exactly 100 fits. A feature is stable if both counts are at least
threshold, fragile if only one reaches threshold. Returns stable and fragile
sorted labels, scores as (label,min_count) sorted by label. Neither batch is
run or validated, and no selection error-rate bound is claimed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
threshold defaults to 80, an exact int from 1 to 100.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: actual resampling, error-rate guarantee, feature truth, count provenance, production readiness.
"""

SCOPE = 'PARTIAL: thresholds supplied inclusion counts out of a fixed 100-fit ensemble'
NOT_CLAIMED = ('actual resampling', 'error-rate guarantee', 'feature truth', 'count provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def stable_features(rows, threshold=80):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(threshold) is not int or not 1 <= threshold <= 100:
        raise ValueError('threshold must be a nonbool integer between 1 and 100')
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
    stable = sorted(n for n, first, second in clean if min(first, second) >= threshold)
    fragile = sorted(n for n, first, second in clean if max(first, second) >= threshold and min(first, second) < threshold)
    scores = [(n, min(first, second)) for n, first, second in sorted(clean, key=lambda r: r[0])]
    return {'stable': stable, 'fragile': fragile, 'scores': scores}
