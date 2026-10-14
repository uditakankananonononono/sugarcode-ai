"""Row 1912, Title: Film Studies

screen_takes(rows): rows are (scene, reel, score) triples;
scene and reel strings of 1 to 16 characters; score a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for
each scene its best score, the natural scenes (first take
already the best, sorted alphabetically), and the climber
(the scene with the largest gain from its first take to
its best among scenes with at least 2 takes, first
supplied on ties, or None when no scene has 2 takes).

SCOPE: PARTIAL: take screening over supplied scores
NOT_CLAIMED: cinematography, editing, sound design,
festival strategy, production readiness.
"""

SCOPE = 'PARTIAL: take screening over supplied scores'
NOT_CLAIMED = ('cinematography', 'editing', 'sound design',
               'festival strategy', 'production readiness')


def screen_takes(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (scene, reel, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        scene, reel, score = row
        if type(scene) is not str or not 1 <= len(scene) <= 16:
            raise ValueError(f'row {i}: scene must be a string of 1 to 16 characters')
        if type(reel) is not str or not 1 <= len(reel) <= 16:
            raise ValueError(f'row {i}: reel must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    firsts = {}
    bests = {}
    counts = {}
    for scene, reel, score in rows:
        if scene not in bests:
            firsts[scene] = score
            bests[scene] = score
            counts[scene] = 0
        if score > bests[scene]:
            bests[scene] = score
        counts[scene] += 1
    natural = sorted(s for s in bests if firsts[s] == bests[s])
    climber = None
    for scene in bests:
        if counts[scene] < 2:
            continue
        if climber is None or bests[scene] - firsts[scene] > bests[climber] - firsts[climber]:
            climber = scene
    return {'total': len(rows),
            'bests': bests,
            'natural': natural,
            'climber': climber}
