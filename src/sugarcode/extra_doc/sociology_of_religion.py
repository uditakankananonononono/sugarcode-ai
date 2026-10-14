"""Row 1901, Title: Sociology of Religion

track_groups(rows): rows are (group, practice, size) triples;
group and practice strings of 1 to 16 characters; size a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for each
group its rises and falls (consecutive rows of that group with
a larger or smaller size than the group's previous row), the
rising groups (more rises than falls, sorted alphabetically),
the falling groups (more falls than rises, sorted
alphabetically), and the steepest group (the most rises,
first supplied on ties).

SCOPE: PARTIAL: group tracking over supplied sizes
NOT_CLAIMED: ethnography, survey sampling, secularization
theory, social network analysis, production readiness.
"""

SCOPE = 'PARTIAL: group tracking over supplied sizes'
NOT_CLAIMED = ('ethnography', 'survey sampling', 'secularization theory',
               'social network analysis', 'production readiness')


def track_groups(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (group, practice, size) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        group, practice, size = row
        if type(group) is not str or not 1 <= len(group) <= 16:
            raise ValueError(f'row {i}: group must be a string of 1 to 16 characters')
        if type(practice) is not str or not 1 <= len(practice) <= 16:
            raise ValueError(f'row {i}: practice must be a string of 1 to 16 characters')
        if type(size) is not int or not 1 <= size <= 9:
            raise ValueError(f'row {i}: size must be a nonbool integer between 1 and 9')
    seen = {}
    rises = {}
    falls = {}
    for group, practice, size in rows:
        if group not in seen:
            seen[group] = size
            rises[group] = 0
            falls[group] = 0
            continue
        if size > seen[group]:
            rises[group] += 1
        elif size < seen[group]:
            falls[group] += 1
        seen[group] = size
    rising = sorted(g for g in rises if rises[g] > falls[g])
    falling = sorted(g for g in rises if falls[g] > rises[g])
    steepest = None
    for group in rises:
        if steepest is None or rises[group] > rises[steepest]:
            steepest = group
    return {'total': len(rows),
            'rises': rises,
            'falls': falls,
            'rising': rising,
            'falling': falling,
            'steepest': steepest}
