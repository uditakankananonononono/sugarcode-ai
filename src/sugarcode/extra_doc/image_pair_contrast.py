"""Row 1121, Medical Image Analysis.

image_pair_contrast accepts supplied paired integer intensities x,y for
caller-named pixel regions. Returns differences as (label,absolute_difference)
sorted by label, changed as labels whose difference strictly exceeds threshold,
maximum as largest difference. No images are read, anatomy identified or
medical significance assigned. Intensities are bounded fixture values only.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
threshold defaults to 10, an exact int from 0 to 100.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: medical image interpretation, lesion detection, diagnosis, pixel provenance, production readiness.
"""

SCOPE = 'PARTIAL: compares supplied paired pixel intensities, no medical image is interpreted'
NOT_CLAIMED = ('medical image interpretation', 'lesion detection', 'diagnosis', 'pixel provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def image_pair_contrast(rows, threshold=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(threshold) is not int or not 0 <= threshold <= 100:
        raise ValueError('threshold must be a nonbool integer between 0 and 100')
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
    differences = [(n, abs(x - y)) for n, x, y in sorted(clean, key=lambda r: r[0])]
    changed = [n for n, d in differences if d > threshold]
    return {'differences': differences, 'changed': changed,
            'maximum': max(d for n, d in differences)}
