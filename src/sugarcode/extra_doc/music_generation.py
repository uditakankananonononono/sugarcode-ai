"""Row 1931, Title: Music Generation

track_variation(rows): rows are (track, composer,
level) triples; track and composer strings of 1 to
16 characters; level a nonbool integer between 1 and
9. Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each composer the
total variation of its level sequence (the summed
absolute step between consecutive levels), the flat
composers (zero variation, sorted alphabetically),
and the roughest composer (the largest variation,
first supplied on ties).

SCOPE: PARTIAL: level variation over supplied rows
NOT_CLAIMED: melody quality, harmony modeling,
arrangement depth, mastering chain, production
readiness.
"""

SCOPE = 'PARTIAL: level variation over supplied rows'
NOT_CLAIMED = ('melody quality', 'harmony modeling',
               'arrangement depth', 'mastering chain',
               'production readiness')


def track_variation(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (track, composer, level) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        track, composer, level = row
        if type(track) is not str or not 1 <= len(track) <= 16:
            raise ValueError(f'row {i}: track must be a string of 1 to 16 characters')
        if type(composer) is not str or not 1 <= len(composer) <= 16:
            raise ValueError(f'row {i}: composer must be a string of 1 to 16 characters')
        if type(level) is not int or not 1 <= level <= 9:
            raise ValueError(f'row {i}: level must be a nonbool integer between 1 and 9')
    seqs = {}
    for track, composer, level in rows:
        if composer not in seqs:
            seqs[composer] = []
        seqs[composer].append(level)
    variation = {}
    for composer in seqs:
        seq = seqs[composer]
        total = 0
        for k in range(1, len(seq)):
            total += abs(seq[k] - seq[k - 1])
        variation[composer] = total
    flat = sorted(c for c in variation if variation[c] == 0)
    roughest = None
    for composer in variation:
        if roughest is None or variation[composer] > variation[roughest]:
            roughest = composer
    return {'total': len(rows),
            'variation': variation,
            'flat': flat,
            'roughest': roughest}
