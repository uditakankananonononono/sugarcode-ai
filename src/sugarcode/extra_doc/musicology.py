"""Row 1910, Title: Musicology

trace_pieces(rows): rows are (piece, composer, tempo) triples;
piece and composer strings of 1 to 16 characters; tempo a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for each
piece its turns (changes of direction in its own tempo
subsequence, ignoring equal steps), the steady pieces (no
turns over at least 2 rows, sorted alphabetically), the
restless pieces (at least 2 turns, sorted alphabetically),
and the wildest piece (the most turns, first supplied on
ties).

SCOPE: PARTIAL: piece tracing over supplied tempos
NOT_CLAIMED: music theory, performance practice, notation,
acoustics, production readiness.
"""

SCOPE = 'PARTIAL: piece tracing over supplied tempos'
NOT_CLAIMED = ('music theory', 'performance practice', 'notation',
               'acoustics', 'production readiness')


def trace_pieces(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (piece, composer, tempo) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        piece, composer, tempo = row
        if type(piece) is not str or not 1 <= len(piece) <= 16:
            raise ValueError(f'row {i}: piece must be a string of 1 to 16 characters')
        if type(composer) is not str or not 1 <= len(composer) <= 16:
            raise ValueError(f'row {i}: composer must be a string of 1 to 16 characters')
        if type(tempo) is not int or not 1 <= tempo <= 9:
            raise ValueError(f'row {i}: tempo must be a nonbool integer between 1 and 9')
    seqs = {}
    for piece, composer, tempo in rows:
        if piece not in seqs:
            seqs[piece] = []
        seqs[piece].append(tempo)
    turns = {}
    counts = {}
    for piece in seqs:
        counts[piece] = len(seqs[piece])
        total_turns = 0
        last_dir = 0
        prev = None
        for tempo in seqs[piece]:
            if prev is not None and tempo != prev:
                d = 1 if tempo > prev else -1
                if last_dir != 0 and d != last_dir:
                    total_turns += 1
                last_dir = d
            prev = tempo
        turns[piece] = total_turns
    steady = sorted(p for p in turns if counts[p] >= 2 and turns[p] == 0)
    restless = sorted(p for p in turns if turns[p] >= 2)
    wildest = None
    for piece in turns:
        if wildest is None or turns[piece] > turns[wildest]:
            wildest = piece
    return {'total': len(rows),
            'turns': turns,
            'steady': steady,
            'restless': restless,
            'wildest': wildest}
