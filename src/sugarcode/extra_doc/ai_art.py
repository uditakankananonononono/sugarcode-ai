"""Row 1934, Title: AI Art

alternating_pull(rows): rows are (piece, studio,
weight) triples; piece and studio strings of 1 to 16
characters; weight a nonbool integer between 1 and
9. Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each studio the
alternating pull of its weight sequence (the first
weight minus the second plus the third, and so on),
the rising studios (a positive pull, sorted
alphabetically), and the strongest studio (the
largest pull, first supplied on ties).

SCOPE: PARTIAL: alternating-pull sums over supplied rows
NOT_CLAIMED: aesthetic judgment, style originality,
training-data provenance, gallery placement,
commercial licensing.
"""

SCOPE = 'PARTIAL: alternating-pull sums over supplied rows'
NOT_CLAIMED = ('aesthetic judgment', 'style originality',
               'training-data provenance', 'gallery placement',
               'commercial licensing')


def alternating_pull(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (piece, studio, weight) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        piece, studio, weight = row
        if type(piece) is not str or not 1 <= len(piece) <= 16:
            raise ValueError(f'row {i}: piece must be a string of 1 to 16 characters')
        if type(studio) is not str or not 1 <= len(studio) <= 16:
            raise ValueError(f'row {i}: studio must be a string of 1 to 16 characters')
        if type(weight) is not int or not 1 <= weight <= 9:
            raise ValueError(f'row {i}: weight must be a nonbool integer between 1 and 9')
    pulls = {}
    counts = {}
    for piece, studio, weight in rows:
        if studio not in pulls:
            pulls[studio] = 0
            counts[studio] = 0
        if counts[studio] % 2 == 0:
            pulls[studio] += weight
        else:
            pulls[studio] -= weight
        counts[studio] += 1
    rising = sorted(s for s in pulls if pulls[s] > 0)
    strongest = None
    for studio in pulls:
        if strongest is None or pulls[studio] > pulls[strongest]:
            strongest = studio
    return {'total': len(rows),
            'pulls': pulls,
            'rising': rising,
            'strongest': strongest}
