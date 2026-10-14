"""Row 1947, Title: AI Safety

count_inversions(rows): rows are (hazard, guard, level)
triples; hazard and guard strings of 1 to 16
characters; level a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each guard its
inversions (pairs of that guard's rows where an
earlier level is strictly above a later one), the
total inversions, and the leader (the most
inversions, first supplied on ties, or None when no
guard has any).

SCOPE: PARTIAL: inversion counting over supplied levels
NOT_CLAIMED: hazard modeling, containment design,
monitoring infrastructure, incident response,
production readiness.
"""

SCOPE = 'PARTIAL: inversion counting over supplied levels'
NOT_CLAIMED = ('hazard modeling', 'containment design',
               'monitoring infrastructure', 'incident response',
               'production readiness')


def count_inversions(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (hazard, guard, level) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        hazard, guard, level = row
        if type(hazard) is not str or not 1 <= len(hazard) <= 16:
            raise ValueError(f'row {i}: hazard must be a string of 1 to 16 characters')
        if type(guard) is not str or not 1 <= len(guard) <= 16:
            raise ValueError(f'row {i}: guard must be a string of 1 to 16 characters')
        if type(level) is not int or not 1 <= level <= 9:
            raise ValueError(f'row {i}: level must be a nonbool integer between 1 and 9')
    seqs = {}
    order = {}
    for hazard, guard, level in rows:
        if guard not in order:
            order[guard] = True
        if guard not in seqs:
            seqs[guard] = []
        seqs[guard].append(level)
    inversions = {}
    total = 0
    for guard in seqs:
        seq = seqs[guard]
        count = 0
        for i in range(len(seq)):
            for j in range(i + 1, len(seq)):
                if seq[i] > seq[j]:
                    count += 1
        if count:
            inversions[guard] = count
            total += count
    leader = None
    for guard in order:
        if guard not in inversions:
            continue
        if leader is None or inversions[guard] > inversions[leader]:
            leader = guard
    return {'total': len(rows),
            'inversions': inversions,
            'pairs': total,
            'leader': leader}
