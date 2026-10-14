"""Row 1134, Length of Stay Prediction.

stay_rounding adds supplied duration components x+y and rounds upward into
caller-sized blocks. Returns durations as sorted (label,sum), blocks as
sorted (label,ceiling(sum/block)), padding as sorted (label,blocks*block-sum).
Zero total needs zero blocks. Units and discharge meaning are not inferred;
this is rounding arithmetic, not length-of-stay or clinical prediction.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
block defaults to 24, an exact int from 1 to 100.
Validation order: rows type, rows size, block, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: patient stay prediction, clinical discharge, time-unit validity, model calibration, production readiness.
"""

SCOPE = 'PARTIAL: rounds caller-supplied duration sums into fixed integer day blocks, no stay is predicted'
NOT_CLAIMED = ('patient stay prediction', 'clinical discharge', 'time-unit validity', 'model calibration', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def stay_rounding(rows, block=24):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(block) is not int or not 1 <= block <= 100:
        raise ValueError('block must be a nonbool integer between 1 and 100')
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
    durations = [(n, first + second) for n, first, second in sorted(clean, key=lambda r: r[0])]
    blocks = [(n, (value + block - 1) // block) for n, value in durations]
    return {'durations': durations, 'blocks': blocks,
            'padding': [(n, count * block - value) for (n, count), (m, value) in zip(blocks, durations)]}
