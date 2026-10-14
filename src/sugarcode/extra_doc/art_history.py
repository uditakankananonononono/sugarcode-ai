"""Row 1907, Title: Art History

crown_periods(rows): rows are (work, period, merit) triples;
work and period strings of 1 to 16 characters; merit a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for each
period its masterpiece (the work with the highest merit,
first supplied on ties), the celebrated periods (a winning
merit of at least 8, sorted alphabetically), the thin periods
(a winning merit of at most 3, sorted alphabetically), and
the finest period (the highest winning merit, first supplied
on ties).

SCOPE: PARTIAL: period crowning over supplied merits
NOT_CLAIMED: provenance, connoisseurship, iconography,
conservation, production readiness.
"""

SCOPE = 'PARTIAL: period crowning over supplied merits'
NOT_CLAIMED = ('provenance', 'connoisseurship', 'iconography',
               'conservation', 'production readiness')


def crown_periods(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (work, period, merit) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        work, period, merit = row
        if type(work) is not str or not 1 <= len(work) <= 16:
            raise ValueError(f'row {i}: work must be a string of 1 to 16 characters')
        if type(period) is not str or not 1 <= len(period) <= 16:
            raise ValueError(f'row {i}: period must be a string of 1 to 16 characters')
        if type(merit) is not int or not 1 <= merit <= 9:
            raise ValueError(f'row {i}: merit must be a nonbool integer between 1 and 9')
    tops = {}
    masters = {}
    for work, period, merit in rows:
        if period not in tops or merit > tops[period]:
            tops[period] = merit
            masters[period] = work
    celebrated = sorted(p for p in tops if tops[p] >= 8)
    thin = sorted(p for p in tops if tops[p] <= 3)
    finest = None
    for period in tops:
        if finest is None or tops[period] > tops[finest]:
            finest = period
    return {'total': len(rows),
            'masters': masters,
            'celebrated': celebrated,
            'thin': thin,
            'finest': finest}
