"""Row 1918, Title: Popular Culture

chase_trends(rows): rows are (meme, platform, heat)
triples; meme and platform strings of 1 to 16 characters;
heat a nonbool integer between 1 and 9. Caps (checked
before any work): 1 to 60 rows. Rows are counted from 1.
Reported: the total row count, for each meme its halftime
row (the earliest row where its running heat first tops
half of its own final total), the quickest meme (the
smallest halftime row, first supplied on ties), and the
slow burns (memes still short of halftime until their own
final row, sorted alphabetically).

SCOPE: PARTIAL: trend chasing over supplied heats
NOT_CLAIMED: meme provenance, platform algorithms,
monetization, demographics, production readiness.
"""

SCOPE = 'PARTIAL: trend chasing over supplied heats'
NOT_CLAIMED = ('meme provenance', 'platform algorithms',
               'monetization', 'demographics', 'production readiness')


def chase_trends(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (meme, platform, heat) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        meme, platform, heat = row
        if type(meme) is not str or not 1 <= len(meme) <= 16:
            raise ValueError(f'row {i}: meme must be a string of 1 to 16 characters')
        if type(platform) is not str or not 1 <= len(platform) <= 16:
            raise ValueError(f'row {i}: platform must be a string of 1 to 16 characters')
        if type(heat) is not int or not 1 <= heat <= 9:
            raise ValueError(f'row {i}: heat must be a nonbool integer between 1 and 9')
    totals = {}
    for meme, platform, heat in rows:
        if meme not in totals:
            totals[meme] = 0
        totals[meme] += heat
    running = {}
    halftime = {}
    last_rows = {}
    for pos, (meme, platform, heat) in enumerate(rows, 1):
        if meme not in running:
            running[meme] = 0
        running[meme] += heat
        if meme not in halftime and running[meme] * 2 > totals[meme]:
            halftime[meme] = pos
        last_rows[meme] = pos
    quickest = None
    for meme in halftime:
        if quickest is None or halftime[meme] < halftime[quickest]:
            quickest = meme
    slow_burn = sorted(m for m in halftime if halftime[m] == last_rows[m])
    return {'total': len(rows),
            'halftime': halftime,
            'quickest': quickest,
            'slow_burn': slow_burn}
