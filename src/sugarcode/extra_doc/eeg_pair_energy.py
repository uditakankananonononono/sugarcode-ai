"""Row 1125, EEG Analysis.

eeg_pair_energy treats x,y as two caller-supplied signed signal samples and
scales them by gain. Returns energy as sorted (label,(gain*x)**2+(gain*y)**2),
difference_energy as sorted (label,(gain*x-gain*y)**2), total as summed energy.
This is two-sample arithmetic, not recording analysis, frequency-band power
or EEG/medical interpretation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
-10 to 10; bool and all subclasses are refused.
gain defaults to 1, an exact int from 1 to 5.
Validation order: rows type, rows size, gain, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: EEG interpretation, seizure detection, spectral bands, signal provenance, production readiness.
"""

SCOPE = 'PARTIAL: computes supplied two-sample energy and difference energy, no EEG recording is analyzed'
NOT_CLAIMED = ('EEG interpretation', 'seizure detection', 'spectral bands', 'signal provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def eeg_pair_energy(rows, gain=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(gain) is not int or not 1 <= gain <= 5:
        raise ValueError('gain must be a nonbool integer between 1 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not -10 <= x <= 10:
            raise ValueError('x must be a nonbool integer between -10 and 10')
        if type(y) is not int or not -10 <= y <= 10:
            raise ValueError('y must be a nonbool integer between -10 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    energy = [(n, gain * gain * (x * x + y * y)) for n, x, y in sorted(clean, key=lambda r: r[0])]
    difference = [(n, gain * gain * (x - y) ** 2) for n, x, y in sorted(clean, key=lambda r: r[0])]
    return {'energy': energy, 'difference_energy': difference,
            'total': sum(v for n, v in energy)}
