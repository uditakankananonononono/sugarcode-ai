"""Row 1930, Title: Text-to-Audio Generation

distinct_tones(rows): rows are (track, generator,
tone) triples; track and generator strings of 1 to
16 characters; tone a nonbool integer between 1 and
9. Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each generator
the number of distinct tones, the varied generators
(every supplied row a new tone, sorted
alphabetically), and the richest generator (the most
distinct tones, first supplied on ties).

SCOPE: PARTIAL: distinct-tone counting over supplied rows
NOT_CLAIMED: audio fidelity, timbre modeling,
sampling quality, licensing clearance, production
readiness.
"""

SCOPE = 'PARTIAL: distinct-tone counting over supplied rows'
NOT_CLAIMED = ('audio fidelity', 'timbre modeling',
               'sampling quality', 'licensing clearance',
               'production readiness')


def distinct_tones(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (track, generator, tone) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        track, generator, tone = row
        if type(track) is not str or not 1 <= len(track) <= 16:
            raise ValueError(f'row {i}: track must be a string of 1 to 16 characters')
        if type(generator) is not str or not 1 <= len(generator) <= 16:
            raise ValueError(f'row {i}: generator must be a string of 1 to 16 characters')
        if type(tone) is not int or not 1 <= tone <= 9:
            raise ValueError(f'row {i}: tone must be a nonbool integer between 1 and 9')
    seen = {}
    supplied = {}
    for track, generator, tone in rows:
        if generator not in seen:
            seen[generator] = set()
            supplied[generator] = 0
        seen[generator].add(tone)
        supplied[generator] += 1
    distinct = {}
    for generator in seen:
        distinct[generator] = len(seen[generator])
    varied = sorted(g for g in distinct if distinct[g] == supplied[g])
    richest = None
    for generator in distinct:
        if richest is None or distinct[generator] > distinct[richest]:
            richest = generator
    return {'total': len(rows),
            'distinct': distinct,
            'varied': varied,
            'richest': richest}
