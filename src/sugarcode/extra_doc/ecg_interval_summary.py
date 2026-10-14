"""Row 1124, ECG Interpretation.

ecg_interval_summary treats x,y as supplied beat-time endpoints in unspecified
integer units, accepts either order. Returns intervals as sorted (label,absolute
time difference), deviations as interval minus supplied target in label order,
irregular as whether interval lengths differ, zero as sorted zero-length labels.
This is interval arithmetic, not ECG waveform interpretation or rhythm diagnosis.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
target defaults to 10, an exact int from 1 to 100.
Validation order: rows type, rows size, target, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: ECG interpretation, arrhythmia diagnosis, clinical thresholds, time provenance, production readiness.
"""

SCOPE = 'PARTIAL: summarizes supplied adjacent beat times, no ECG waveform is interpreted'
NOT_CLAIMED = ('ECG interpretation', 'arrhythmia diagnosis', 'clinical thresholds', 'time provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ecg_interval_summary(rows, target=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(target) is not int or not 1 <= target <= 100:
        raise ValueError('target must be a nonbool integer between 1 and 100')
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
    intervals = [(n, abs(end - start)) for n, start, end in sorted(clean, key=lambda r: r[0])]
    deviations = [(n, gap - target) for n, gap in intervals]
    return {'intervals': intervals, 'deviations': deviations,
            'irregular': len({gap for n, gap in intervals}) > 1,
            'zero': [n for n, gap in intervals if gap == 0]}
