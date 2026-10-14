"""Row 1118, Treatment Protocol Selection.

protocol_windows treats x,y as caller-written inclusive applicability
endpoints in either order. Return matches as (label,width) for windows
containing marker, narrowest first then label; excluded as sorted labels
outside marker; ambiguous as whether more than one window matches. It does
not pick a protocol, assign clinical meaning or advise treatment.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
marker defaults to 50, an exact int from 0 to 100.
Validation order: rows type, rows size, marker, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: treatment selection, clinical safety, guideline validity, patient applicability, production readiness.
"""

SCOPE = 'PARTIAL: filters caller-supplied applicability windows for one integer marker, no treatment is selected'
NOT_CLAIMED = ('treatment selection', 'clinical safety', 'guideline validity', 'patient applicability', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def protocol_windows(rows, marker=50):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(marker) is not int or not 0 <= marker <= 100:
        raise ValueError('marker must be a nonbool integer between 0 and 100')
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
    windows = [(n, min(x, y), max(x, y)) for n, x, y in sorted(clean, key=lambda r: r[0])]
    matches = [(n, hi - lo) for n, lo, hi in windows if lo <= marker <= hi]
    matches.sort(key=lambda r: (r[1], r[0]))
    return {'matches': matches, 'excluded': [n for n, lo, hi in windows if not lo <= marker <= hi],
            'ambiguous': len(matches) > 1}
