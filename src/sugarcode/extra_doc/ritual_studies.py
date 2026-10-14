"""Row 1906, Title: Ritual Studies

weigh_rites(rows): rows are (rite, officiant, solemnity)
triples; rite and officiant strings of 1 to 16 characters;
solemnity a nonbool integer between 1 and 9. Caps (checked
before any work): 1 to 60 rows. Reported: the total row count,
for each rite its odd and even solemnity counts, the
odd-leaning rites (more odd than even rows, sorted
alphabetically), the even-leaning rites (more even than odd
rows, sorted alphabetically), and the oddest rite (the most
odd rows, first supplied on ties).

SCOPE: PARTIAL: rite weighing over supplied solemnities
NOT_CLAIMED: liturgy, ritual efficacy, sacred time,
initiation rites, production readiness.
"""

SCOPE = 'PARTIAL: rite weighing over supplied solemnities'
NOT_CLAIMED = ('liturgy', 'ritual efficacy', 'sacred time',
               'initiation rites', 'production readiness')


def weigh_rites(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (rite, officiant, solemnity) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        rite, officiant, solemnity = row
        if type(rite) is not str or not 1 <= len(rite) <= 16:
            raise ValueError(f'row {i}: rite must be a string of 1 to 16 characters')
        if type(officiant) is not str or not 1 <= len(officiant) <= 16:
            raise ValueError(f'row {i}: officiant must be a string of 1 to 16 characters')
        if type(solemnity) is not int or not 1 <= solemnity <= 9:
            raise ValueError(f'row {i}: solemnity must be a nonbool integer between 1 and 9')
    odds = {}
    evens = {}
    for rite, officiant, solemnity in rows:
        if rite not in odds:
            odds[rite] = 0
            evens[rite] = 0
        if solemnity % 2 == 1:
            odds[rite] += 1
        else:
            evens[rite] += 1
    odd_leaning = sorted(r for r in odds if odds[r] > evens[r])
    even_leaning = sorted(r for r in odds if evens[r] > odds[r])
    oddest = None
    for rite in odds:
        if oddest is None or odds[rite] > odds[oddest]:
            oddest = rite
    return {'total': len(rows),
            'odds': odds,
            'evens': evens,
            'odd_leaning': odd_leaning,
            'even_leaning': even_leaning,
            'oddest': oddest}
