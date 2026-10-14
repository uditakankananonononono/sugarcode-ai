"""Row 1099, LightGBM - Fast gradient boosting.

histogram_split bins feature x by floor(x/binsize), target y. Candidate
splits are each occupied bin except the largest. Compute total within-child
squared-error loss for a constant mean in each child. Returns splits as
(bin,Fraction loss string) by ascending bin, best as lowest-loss bin with
smallest-bin ties or None, left as sorted labels assigned to best's left
child or empty with no split. This is one histogram split kernel only.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
binsize defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, binsize, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: LightGBM training, leaf-wise growth, generalization, histogram adequacy, production readiness.
"""

SCOPE = 'PARTIAL: chooses a histogram-bin squared-error split from supplied samples, no LightGBM is trained'
NOT_CLAIMED = ('LightGBM training', 'leaf-wise growth', 'generalization', 'histogram adequacy', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def histogram_split(rows, binsize=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(binsize) is not int or not 1 <= binsize <= 5:
        raise ValueError('binsize must be a nonbool integer between 1 and 5')
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
    from fractions import Fraction as F
    nodes = [(n, x // binsize, y) for n, x, y in clean]
    candidates = sorted({b for n, b, y in nodes})[:-1]
    splits = []
    for b in candidates:
        left = [y for n, k, y in nodes if k <= b]
        right = [y for n, k, y in nodes if k > b]
        loss = sum(F(sum(v*v for v in side)) - F(sum(side) ** 2, len(side)) for side in (left, right))
        splits.append((b, loss))
    best = min(splits, key=lambda r: (r[1], r[0]))[0] if splits else None
    return {'splits': [(b, str(loss)) for b, loss in splits], 'best': best,
            'left': sorted(n for n, b, y in nodes if best is not None and b <= best)}
