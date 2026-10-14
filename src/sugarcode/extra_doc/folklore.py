"""Row 1905, Title: Folklore

trace_motifs(rows): rows are (tale, motif, charm) triples;
tale and motif strings of 1 to 16 characters; charm a nonbool
integer between 1 and 9. Caps (checked before any work): 1 to
60 rows. Reported: the total row count, the echoes (adjacent
row pairs sharing one motif), the echoing motifs (the motifs
of those pairs, sorted alphabetically), for each tale the
total charm, and the richest tale (the largest total, first
supplied on ties).

SCOPE: PARTIAL: motif tracing over supplied charms
NOT_CLAIMED: oral tradition, tale typing, fieldwork,
performance studies, production readiness.
"""

SCOPE = 'PARTIAL: motif tracing over supplied charms'
NOT_CLAIMED = ('oral tradition', 'tale typing', 'fieldwork',
               'performance studies', 'production readiness')


def trace_motifs(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (tale, motif, charm) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        tale, motif, charm = row
        if type(tale) is not str or not 1 <= len(tale) <= 16:
            raise ValueError(f'row {i}: tale must be a string of 1 to 16 characters')
        if type(motif) is not str or not 1 <= len(motif) <= 16:
            raise ValueError(f'row {i}: motif must be a string of 1 to 16 characters')
        if type(charm) is not int or not 1 <= charm <= 9:
            raise ValueError(f'row {i}: charm must be a nonbool integer between 1 and 9')
    echoes = 0
    marked = {}
    for j in range(len(rows) - 1):
        if rows[j][1] == rows[j + 1][1]:
            echoes += 1
            marked[rows[j][1]] = True
    echoing = sorted(marked)
    totals = {}
    for tale, motif, charm in rows:
        if tale not in totals:
            totals[tale] = 0
        totals[tale] += charm
    richest = None
    for tale in totals:
        if richest is None or totals[tale] > totals[richest]:
            richest = tale
    return {'total': len(rows),
            'echoes': echoes,
            'echoing': echoing,
            'totals': totals,
            'richest': richest}
