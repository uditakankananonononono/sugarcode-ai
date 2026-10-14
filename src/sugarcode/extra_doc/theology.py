"""Row 1898, Title: Theology

weigh_doctrines(rows): rows are (doctrine, school, weight)
triples; doctrine and school strings of 1 to 16 characters;
weight a nonbool integer between 1 and 9. Caps (checked before
any work): 1 to 60 rows. Reported: the total row count, for
each doctrine its drift (the last weight minus the first), the
hardened doctrines (drift at least 3, sorted alphabetically),
the softened doctrines (drift at most -3, sorted
alphabetically), and the volatile doctrine (the largest
absolute drift, first supplied on ties).

SCOPE: PARTIAL: doctrine weighing over supplied weights
NOT_CLAIMED: systematic theology, exegesis, dogmatics,
historical criticism, production readiness.
"""

SCOPE = 'PARTIAL: doctrine weighing over supplied weights'
NOT_CLAIMED = ('systematic theology', 'exegesis', 'dogmatics',
               'historical criticism', 'production readiness')


def weigh_doctrines(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (doctrine, school, weight) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        doctrine, school, weight = row
        if type(doctrine) is not str or not 1 <= len(doctrine) <= 16:
            raise ValueError(f'row {i}: doctrine must be a string of 1 to 16 characters')
        if type(school) is not str or not 1 <= len(school) <= 16:
            raise ValueError(f'row {i}: school must be a string of 1 to 16 characters')
        if type(weight) is not int or not 1 <= weight <= 9:
            raise ValueError(f'row {i}: weight must be a nonbool integer between 1 and 9')
    first = {}
    last = {}
    for doctrine, school, weight in rows:
        if doctrine not in first:
            first[doctrine] = weight
        last[doctrine] = weight
    drifts = {}
    for doctrine in first:
        drifts[doctrine] = last[doctrine] - first[doctrine]
    hardened = sorted(d for d in drifts if drifts[d] >= 3)
    softened = sorted(d for d in drifts if drifts[d] <= -3)
    volatile = None
    for doctrine in drifts:
        if volatile is None or abs(drifts[doctrine]) > abs(drifts[volatile]):
            volatile = doctrine
    return {'total': len(rows),
            'drifts': drifts,
            'hardened': hardened,
            'softened': softened,
            'volatile': volatile}
