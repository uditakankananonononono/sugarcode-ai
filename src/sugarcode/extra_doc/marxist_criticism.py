"""Row 1877, Title: Marxist Criticism

class_struggle(rows): rows are (work, faction, wealth) triples;
work and faction strings of 1 to 16 characters; wealth a nonbool
integer between 1 and 9. Caps (checked before any work): 1 to 60
rows. Reported: the total row count, for each work the gap between
its richest and poorest faction totals, the polarized works (gap
at least 7, sorted alphabetically), the egalitarian works (gap of
zero, sorted alphabetically), and the work with the widest gap
(first supplied on ties).

SCOPE: PARTIAL: wealth-gap tallying over supplied factions
NOT_CLAIMED: historical materialism, class consciousness,
ideology critique, economic determinism, production readiness.
"""

SCOPE = 'PARTIAL: wealth-gap tallying over supplied factions'
NOT_CLAIMED = ('historical materialism', 'class consciousness',
               'ideology critique', 'economic determinism',
               'production readiness')


def class_struggle(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (work, faction, wealth) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        work, faction, wealth = row
        if type(work) is not str or not 1 <= len(work) <= 16:
            raise ValueError(f'row {i}: work must be a string of 1 to 16 characters')
        if type(faction) is not str or not 1 <= len(faction) <= 16:
            raise ValueError(f'row {i}: faction must be a string of 1 to 16 characters')
        if type(wealth) is not int or not 1 <= wealth <= 9:
            raise ValueError(f'row {i}: wealth must be a nonbool integer between 1 and 9')
    holdings = {}
    for work, faction, wealth in rows:
        if work not in holdings:
            holdings[work] = {}
        if faction not in holdings[work]:
            holdings[work][faction] = 0
        holdings[work][faction] += wealth
    gap = {}
    for work in holdings:
        richest = None
        for faction in holdings[work]:
            if richest is None or holdings[work][faction] > richest:
                richest = holdings[work][faction]
        poorest = None
        for faction in holdings[work]:
            if poorest is None or holdings[work][faction] < poorest:
                poorest = holdings[work][faction]
        gap[work] = richest - poorest
    polarized = sorted(work for work in gap if gap[work] >= 7)
    egalitarian = sorted(work for work in gap if gap[work] == 0)
    widest = None
    for work in gap:
        if widest is None or gap[work] > gap[widest]:
            widest = work
    return {'total': len(rows),
            'gap': gap,
            'polarized': polarized,
            'egalitarian': egalitarian,
            'widest': widest}
