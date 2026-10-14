"""Row 1873, Title: Narrative Theory

track_voices(rows): rows are (scene, voice, intensity) triples;
scene and voice strings of 1 to 16 characters; intensity a nonbool
integer between 1 and 9. Caps (checked before any work): 1 to 60
rows. Reported: the total row count, for each voice the number of
scenes, the switches (adjacent rows in the supplied order where the
voice changes), the longest run (the most consecutive rows sharing
one voice), and the dominant voice (the most scenes, first supplied
on ties).

SCOPE: PARTIAL: voice tracking over supplied scenes
NOT_CLAIMED: real narration, focalization theory, authorial intent,
reader interpretation, production readiness.
"""

SCOPE = 'PARTIAL: voice tracking over supplied scenes'
NOT_CLAIMED = ('real narration', 'focalization theory',
               'authorial intent', 'reader interpretation',
               'production readiness')


def track_voices(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (scene, voice, intensity) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        scene, voice, intensity = row
        if type(scene) is not str or not 1 <= len(scene) <= 16:
            raise ValueError(f'row {i}: scene must be a string of 1 to 16 characters')
        if type(voice) is not str or not 1 <= len(voice) <= 16:
            raise ValueError(f'row {i}: voice must be a string of 1 to 16 characters')
        if type(intensity) is not int or not 1 <= intensity <= 9:
            raise ValueError(f'row {i}: intensity must be a nonbool integer between 1 and 9')
    scenes = {}
    switches = 0
    longest = 0
    streak = 0
    previous = None
    for scene, voice, intensity in rows:
        if voice not in scenes:
            scenes[voice] = 0
        scenes[voice] += 1
        if previous is None or voice == previous:
            streak += 1
        else:
            switches += 1
            streak = 1
        if streak > longest:
            longest = streak
        previous = voice
    dominant = None
    for voice in scenes:
        if dominant is None or scenes[voice] > scenes[dominant]:
            dominant = voice
    return {'total': len(rows),
            'scenes': scenes,
            'switches': switches,
            'longest': longest,
            'dominant': dominant}
