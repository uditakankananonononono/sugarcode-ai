"""Row 1869, Title: Drama

pace_scenes(rows): rows are (play, scene, lines) triples; play and
scene strings of 1 to 16 characters; lines a nonbool integer
between 1 and 99. Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each play the number of scenes,
for each play the rises and falls (strict increases and strict
decreases between adjacent scenes in the supplied order), the
building plays (more rises than falls) in ascending order, the
falling plays (more falls than rises) in ascending order, and the
steadiest play (the fewest rises plus falls across at least two
scenes, first supplied on ties).

SCOPE: PARTIAL: scene pacing over supplied line counts
NOT_CLAIMED: real dramaturgy, staging quality, performance success,
playwright intent, production readiness.
"""

SCOPE = 'PARTIAL: scene pacing over supplied line counts'
NOT_CLAIMED = ('real dramaturgy', 'staging quality',
               'performance success', 'playwright intent',
               'production readiness')


def pace_scenes(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (play, scene, lines) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        play, scene, lines = row
        if type(play) is not str or not 1 <= len(play) <= 16:
            raise ValueError(f'row {i}: play must be a string of 1 to 16 characters')
        if type(scene) is not str or not 1 <= len(scene) <= 16:
            raise ValueError(f'row {i}: scene must be a string of 1 to 16 characters')
        if type(lines) is not int or not 1 <= lines <= 99:
            raise ValueError(f'row {i}: lines must be a nonbool integer between 1 and 99')
    scenes = {}
    rises = {}
    falls = {}
    previous = {}
    for play, scene, lines in rows:
        if play not in scenes:
            scenes[play] = 0
            rises[play] = 0
            falls[play] = 0
        scenes[play] += 1
        if play in previous:
            if lines > previous[play]:
                rises[play] += 1
            elif lines < previous[play]:
                falls[play] += 1
        previous[play] = lines
    building = sorted(p for p in scenes if rises[p] > falls[p])
    falling = sorted(p for p in scenes if falls[p] > rises[p])
    steadiest = None
    for play in scenes:
        if scenes[play] < 2:
            continue
        if (steadiest is None
                or rises[play] + falls[play]
                < rises[steadiest] + falls[steadiest]):
            steadiest = play
    return {'total': len(rows),
            'scenes': scenes,
            'rises': rises,
            'falls': falls,
            'building': building,
            'falling': falling,
            'steadiest': steadiest}
