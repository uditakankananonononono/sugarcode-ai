"""Row 1897, Title: Religion

survey_traditions(rows): rows are (tradition, practice,
adherents) triples; tradition and practice strings of 1 to 16
characters; adherents a nonbool integer between 1 and 9. Caps
(checked before any work): 1 to 60 rows. Reported: the total
row count, for each tradition the total adherents, the streak
(the first longest run of consecutive rows naming one
tradition, as its tradition and length), the widespread
traditions (at least 3 rows, sorted alphabetically), and the
devoted tradition (the largest total, first supplied on ties).

SCOPE: PARTIAL: tradition surveying over supplied tallies
NOT_CLAIMED: theology, comparative belief, ritual practice,
census accuracy, production readiness.
"""

SCOPE = 'PARTIAL: tradition surveying over supplied tallies'
NOT_CLAIMED = ('theology', 'comparative belief', 'ritual practice',
               'census accuracy', 'production readiness')


def survey_traditions(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (tradition, practice, adherents) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        tradition, practice, adherents = row
        if type(tradition) is not str or not 1 <= len(tradition) <= 16:
            raise ValueError(f'row {i}: tradition must be a string of 1 to 16 characters')
        if type(practice) is not str or not 1 <= len(practice) <= 16:
            raise ValueError(f'row {i}: practice must be a string of 1 to 16 characters')
        if type(adherents) is not int or not 1 <= adherents <= 9:
            raise ValueError(f'row {i}: adherents must be a nonbool integer between 1 and 9')
    totals = {}
    counts = {}
    for tradition, practice, adherents in rows:
        if tradition not in totals:
            totals[tradition] = 0
            counts[tradition] = 0
        totals[tradition] += adherents
        counts[tradition] += 1
    streak_tradition = rows[0][0]
    streak_length = 1
    run_tradition = rows[0][0]
    run_length = 1
    for tradition, practice, adherents in rows[1:]:
        if tradition == run_tradition:
            run_length += 1
        else:
            run_tradition = tradition
            run_length = 1
        if run_length > streak_length:
            streak_tradition = run_tradition
            streak_length = run_length
    widespread = sorted(t for t in counts if counts[t] >= 3)
    devoted = None
    for tradition in totals:
        if devoted is None or totals[tradition] > totals[devoted]:
            devoted = tradition
    return {'total': len(rows),
            'totals': totals,
            'streak': {'tradition': streak_tradition, 'length': streak_length},
            'widespread': widespread,
            'devoted': devoted}
