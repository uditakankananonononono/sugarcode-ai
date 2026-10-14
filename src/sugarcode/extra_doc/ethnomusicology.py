"""Row 1911, Title: Ethnomusicology

weigh_regions(rows): rows are (song, region, length) triples;
song and region strings of 1 to 16 characters; length a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for each
region the total length, the majority region (a total
strictly greater than all other regions combined, None when
none), the fringe regions (total at most 4, sorted
alphabetically), and the plurality region (the largest
total, first supplied on ties).

SCOPE: PARTIAL: region weighing over supplied lengths
NOT_CLAIMED: fieldwork, organology, transcription,
cultural ownership, production readiness.
"""

SCOPE = 'PARTIAL: region weighing over supplied lengths'
NOT_CLAIMED = ('fieldwork', 'organology', 'transcription',
               'cultural ownership', 'production readiness')


def weigh_regions(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (song, region, length) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        song, region, length = row
        if type(song) is not str or not 1 <= len(song) <= 16:
            raise ValueError(f'row {i}: song must be a string of 1 to 16 characters')
        if type(region) is not str or not 1 <= len(region) <= 16:
            raise ValueError(f'row {i}: region must be a string of 1 to 16 characters')
        if type(length) is not int or not 1 <= length <= 9:
            raise ValueError(f'row {i}: length must be a nonbool integer between 1 and 9')
    totals = {}
    for song, region, length in rows:
        if region not in totals:
            totals[region] = 0
        totals[region] += length
    grand = sum(totals.values())
    majority = None
    for region in totals:
        if totals[region] > grand - totals[region]:
            majority = region
    fringe = sorted(r for r in totals if totals[r] <= 4)
    plurality = None
    for region in totals:
        if plurality is None or totals[region] > totals[plurality]:
            plurality = region
    return {'total': len(rows),
            'totals': totals,
            'majority': majority,
            'fringe': fringe,
            'plurality': plurality}
