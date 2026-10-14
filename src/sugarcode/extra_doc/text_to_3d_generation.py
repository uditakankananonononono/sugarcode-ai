"""Row 1929, Title: Text-to-3D Generation

fuse_steps(rows): rows are (asset, engine, steps)
triples; asset and engine strings of 1 to 16
characters; steps a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each engine the
bitwise xor of its step values, the balanced engines
(whose xor cancels to zero, sorted alphabetically),
and the sharpest engine (the largest xor, first
supplied on ties).

SCOPE: PARTIAL: xor fusion over supplied step values
NOT_CLAIMED: mesh quality, texture synthesis,
geometry consistency, render cost, production
readiness.
"""

SCOPE = 'PARTIAL: xor fusion over supplied step values'
NOT_CLAIMED = ('mesh quality', 'texture synthesis',
               'geometry consistency', 'render cost',
               'production readiness')


def fuse_steps(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (asset, engine, steps) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        asset, engine, steps = row
        if type(asset) is not str or not 1 <= len(asset) <= 16:
            raise ValueError(f'row {i}: asset must be a string of 1 to 16 characters')
        if type(engine) is not str or not 1 <= len(engine) <= 16:
            raise ValueError(f'row {i}: engine must be a string of 1 to 16 characters')
        if type(steps) is not int or not 1 <= steps <= 9:
            raise ValueError(f'row {i}: steps must be a nonbool integer between 1 and 9')
    xors = {}
    for asset, engine, steps in rows:
        if engine not in xors:
            xors[engine] = 0
        xors[engine] ^= steps
    balanced = sorted(e for e in xors if xors[e] == 0)
    sharpest = None
    for engine in xors:
        if sharpest is None or xors[engine] > xors[sharpest]:
            sharpest = engine
    return {'total': len(rows),
            'xors': xors,
            'balanced': balanced,
            'sharpest': sharpest}
