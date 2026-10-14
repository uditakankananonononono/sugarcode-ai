"""Row 1868, Title: Poetry

scan_couplets(rows): rows are (poem, line, rhyme) triples; poem and
line strings of 1 to 16 characters; rhyme a nonbool integer between
1 and 9 naming a rhyme class. Caps (checked before any work): 1 to
60 rows. Reported: the total row count, for each poem the number of
lines, for each poem the number of couplets (adjacent lines in the
supplied order sharing a rhyme class), the unrhymed poems (no
couplets across at least two lines) in ascending order, and the
richest poem (the most couplets, first supplied on ties).

SCOPE: PARTIAL: couplet scanning over supplied rhyme classes
NOT_CLAIMED: real prosody, poetic merit, phonetic analysis,
compositional advice, production readiness.
"""

SCOPE = 'PARTIAL: couplet scanning over supplied rhyme classes'
NOT_CLAIMED = ('real prosody', 'poetic merit', 'phonetic analysis',
               'compositional advice', 'production readiness')


def scan_couplets(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (poem, line, rhyme) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        poem, line, rhyme = row
        if type(poem) is not str or not 1 <= len(poem) <= 16:
            raise ValueError(f'row {i}: poem must be a string of 1 to 16 characters')
        if type(line) is not str or not 1 <= len(line) <= 16:
            raise ValueError(f'row {i}: line must be a string of 1 to 16 characters')
        if type(rhyme) is not int or not 1 <= rhyme <= 9:
            raise ValueError(f'row {i}: rhyme must be a nonbool integer between 1 and 9')
    lines = {}
    couplets = {}
    previous = {}
    for poem, line, rhyme in rows:
        if poem not in lines:
            lines[poem] = 0
        lines[poem] += 1
        if poem not in couplets:
            couplets[poem] = 0
        if poem in previous and previous[poem] == rhyme:
            couplets[poem] += 1
        previous[poem] = rhyme
    unrhymed = sorted(p for p in lines
                      if lines[p] >= 2 and couplets[p] == 0)
    richest = None
    for poem in couplets:
        if richest is None or couplets[poem] > couplets[richest]:
            richest = poem
    return {'total': len(rows),
            'lines': lines,
            'couplets': couplets,
            'unrhymed': unrhymed,
            'richest': richest}
