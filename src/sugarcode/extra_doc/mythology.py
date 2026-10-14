"""Row 1904, Title: Mythology

rank_heroes(rows): rows are (hero, myth, power) triples; hero
and myth strings of 1 to 16 characters; power a nonbool
integer between 1 and 9. Caps (checked before any work): 1 to
60 rows. Reported: the total row count, for each hero its
floor (the lowest power across its rows), the unbeaten heroes
(floor at least 7, sorted alphabetically), the fragile heroes
(floor at most 2, sorted alphabetically), and the sturdiest
hero (the highest floor, first supplied on ties).

SCOPE: PARTIAL: hero ranking over supplied powers
NOT_CLAIMED: mythography, archetypes, comparative mythology,
cult practice, production readiness.
"""

SCOPE = 'PARTIAL: hero ranking over supplied powers'
NOT_CLAIMED = ('mythography', 'archetypes', 'comparative mythology',
               'cult practice', 'production readiness')


def rank_heroes(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (hero, myth, power) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        hero, myth, power = row
        if type(hero) is not str or not 1 <= len(hero) <= 16:
            raise ValueError(f'row {i}: hero must be a string of 1 to 16 characters')
        if type(myth) is not str or not 1 <= len(myth) <= 16:
            raise ValueError(f'row {i}: myth must be a string of 1 to 16 characters')
        if type(power) is not int or not 1 <= power <= 9:
            raise ValueError(f'row {i}: power must be a nonbool integer between 1 and 9')
    floors = {}
    for hero, myth, power in rows:
        if hero not in floors:
            floors[hero] = power
        elif power < floors[hero]:
            floors[hero] = power
    unbeaten = sorted(h for h in floors if floors[h] >= 7)
    fragile = sorted(h for h in floors if floors[h] <= 2)
    sturdiest = None
    for hero in floors:
        if sturdiest is None or floors[hero] > floors[sturdiest]:
            sturdiest = hero
    return {'total': len(rows),
            'floors': floors,
            'unbeaten': unbeaten,
            'fragile': fragile,
            'sturdiest': sturdiest}
