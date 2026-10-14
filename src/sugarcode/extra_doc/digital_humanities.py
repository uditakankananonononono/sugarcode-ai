"""Row 1922, Title: Digital Humanities

mark_flawless(rows): rows are (corpus, tool, gain) triples;
corpus and tool strings of 1 to 16 characters; gain a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for
each corpus its nines (rows gaining the top value 9),
the polished corpora (at least 2 rows and every row a 9,
sorted alphabetically), and the most nines (the corpus
with the most nines, first supplied on ties).

SCOPE: PARTIAL: flawless marking over supplied gains
NOT_CLAIMED: corpus linguistics, digitization ethics,
archival policy, tool benchmarking, production readiness.
"""

SCOPE = 'PARTIAL: flawless marking over supplied gains'
NOT_CLAIMED = ('corpus linguistics', 'digitization ethics',
               'archival policy', 'tool benchmarking',
               'production readiness')


def mark_flawless(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (corpus, tool, gain) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        corpus, tool, gain = row
        if type(corpus) is not str or not 1 <= len(corpus) <= 16:
            raise ValueError(f'row {i}: corpus must be a string of 1 to 16 characters')
        if type(tool) is not str or not 1 <= len(tool) <= 16:
            raise ValueError(f'row {i}: tool must be a string of 1 to 16 characters')
        if type(gain) is not int or not 1 <= gain <= 9:
            raise ValueError(f'row {i}: gain must be a nonbool integer between 1 and 9')
    counts = {}
    nines = {}
    for corpus, tool, gain in rows:
        if corpus not in counts:
            counts[corpus] = 0
            nines[corpus] = 0
        counts[corpus] += 1
        if gain == 9:
            nines[corpus] += 1
    polished = sorted(c for c in counts
                      if counts[c] >= 2 and nines[c] == counts[c])
    most_nines = None
    for corpus in nines:
        if most_nines is None or nines[corpus] > nines[most_nines]:
            most_nines = corpus
    return {'total': len(rows),
            'nines': nines,
            'polished': polished,
            'most_nines': most_nines}
