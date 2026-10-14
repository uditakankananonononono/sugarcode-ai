"""Row 1921, Title: Heritage Studies

gauge_care(rows): rows are (site, region, care) triples;
site and region strings of 1 to 16 characters; care a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for
each site its declines (rows whose care falls strictly
below that site's own first row), the steady sites (no
declines, sorted alphabetically), and the worst site
(the most declines, first supplied on ties).

SCOPE: PARTIAL: care gauging over supplied readings
NOT_CLAIMED: restoration practice, funding policy,
tourism impact, legal protection, production readiness.
"""

SCOPE = 'PARTIAL: care gauging over supplied readings'
NOT_CLAIMED = ('restoration practice', 'funding policy',
               'tourism impact', 'legal protection',
               'production readiness')


def gauge_care(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (site, region, care) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        site, region, care = row
        if type(site) is not str or not 1 <= len(site) <= 16:
            raise ValueError(f'row {i}: site must be a string of 1 to 16 characters')
        if type(region) is not str or not 1 <= len(region) <= 16:
            raise ValueError(f'row {i}: region must be a string of 1 to 16 characters')
        if type(care) is not int or not 1 <= care <= 9:
            raise ValueError(f'row {i}: care must be a nonbool integer between 1 and 9')
    baseline = {}
    declines = {}
    for site, region, care in rows:
        if site not in baseline:
            baseline[site] = care
            declines[site] = 0
        elif care < baseline[site]:
            declines[site] += 1
    steady = sorted(s for s in declines if declines[s] == 0)
    worst = None
    for site in declines:
        if worst is None or declines[site] > declines[worst]:
            worst = site
    return {'total': len(rows),
            'declines': declines,
            'steady': steady,
            'worst': worst}
