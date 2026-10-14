"""Row 1915, Title: Dance Studies

read_levels(rows): rows are (move, crew, power) triples;
move and crew strings of 1 to 16 characters; power a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for
each used power level its row count (first use order),
the missing levels (values from 1 to 9 with no rows,
sorted ascending), and the broadest level (the power
used by the most distinct crews, first used on ties).

SCOPE: PARTIAL: level reading over supplied powers
NOT_CLAIMED: choreography, technique, injury prevention,
stage lighting, production readiness.
"""

SCOPE = 'PARTIAL: level reading over supplied powers'
NOT_CLAIMED = ('choreography', 'technique', 'injury prevention',
               'stage lighting', 'production readiness')


def read_levels(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (move, crew, power) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        move, crew, power = row
        if type(move) is not str or not 1 <= len(move) <= 16:
            raise ValueError(f'row {i}: move must be a string of 1 to 16 characters')
        if type(crew) is not str or not 1 <= len(crew) <= 16:
            raise ValueError(f'row {i}: crew must be a string of 1 to 16 characters')
        if type(power) is not int or not 1 <= power <= 9:
            raise ValueError(f'row {i}: power must be a nonbool integer between 1 and 9')
    levels = {}
    crews = {}
    for move, crew, power in rows:
        if power not in levels:
            levels[power] = 0
            crews[power] = {}
        levels[power] += 1
        crews[power][crew] = True
    missing = sorted(p for p in range(1, 10) if p not in levels)
    broadest = None
    for power in levels:
        if broadest is None or len(crews[power]) > len(crews[broadest]):
            broadest = power
    return {'total': len(rows),
            'levels': levels,
            'missing': missing,
            'broadest': broadest}
