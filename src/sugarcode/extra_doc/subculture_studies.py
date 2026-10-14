"""Row 1919, Title: Subculture Studies

read_scenes(rows): rows are (scene, zine, buzz) triples;
scene and zine strings of 1 to 16 characters; buzz a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, the
overlap (buzz values used by at least 2 distinct scenes,
sorted ascending), for each scene its signature (the
buzz values no other scene uses, sorted ascending), and
the most signed scene (the longest signature, first
supplied on ties).

SCOPE: PARTIAL: scene reading over supplied buzzes
NOT_CLAIMED: gatekeeping, fashion history, music
criticism, online moderation, production readiness.
"""

SCOPE = 'PARTIAL: scene reading over supplied buzzes'
NOT_CLAIMED = ('gatekeeping', 'fashion history', 'music criticism',
               'online moderation', 'production readiness')


def read_scenes(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (scene, zine, buzz) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        scene, zine, buzz = row
        if type(scene) is not str or not 1 <= len(scene) <= 16:
            raise ValueError(f'row {i}: scene must be a string of 1 to 16 characters')
        if type(zine) is not str or not 1 <= len(zine) <= 16:
            raise ValueError(f'row {i}: zine must be a string of 1 to 16 characters')
        if type(buzz) is not int or not 1 <= buzz <= 9:
            raise ValueError(f'row {i}: buzz must be a nonbool integer between 1 and 9')
    values = {}
    for scene, zine, buzz in rows:
        if scene not in values:
            values[scene] = {}
        values[scene][buzz] = True
    overlap = sorted(b for b in range(1, 10)
                     if sum(1 for s in values if b in values[s]) >= 2)
    signature = {}
    for scene in values:
        signature[scene] = sorted(b for b in values[scene]
                                  if sum(1 for s in values if b in values[s]) == 1)
    most_signed = None
    for scene in signature:
        if most_signed is None or len(signature[scene]) > len(signature[most_signed]):
            most_signed = scene
    return {'total': len(rows),
            'overlap': overlap,
            'signature': signature,
            'most_signed': most_signed}
