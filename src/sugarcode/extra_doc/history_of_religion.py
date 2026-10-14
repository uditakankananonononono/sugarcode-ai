"""Row 1900, Title: History of Religion

chart_eras(rows): rows are (era, event, significance) triples;
era and event strings of 1 to 16 characters; significance a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for each
era its average significance (the floored total over its row
count), the golden eras (average at least 7, sorted
alphabetically), the dark eras (average at most 3, sorted
alphabetically), and the zenith era (the highest average,
first supplied on ties).

SCOPE: PARTIAL: era charting over supplied significances
NOT_CLAIMED: periodization, historiography, source criticism,
causation, production readiness.
"""

SCOPE = 'PARTIAL: era charting over supplied significances'
NOT_CLAIMED = ('periodization', 'historiography', 'source criticism',
               'causation', 'production readiness')


def chart_eras(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (era, event, significance) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        era, event, significance = row
        if type(era) is not str or not 1 <= len(era) <= 16:
            raise ValueError(f'row {i}: era must be a string of 1 to 16 characters')
        if type(event) is not str or not 1 <= len(event) <= 16:
            raise ValueError(f'row {i}: event must be a string of 1 to 16 characters')
        if type(significance) is not int or not 1 <= significance <= 9:
            raise ValueError(f'row {i}: significance must be a nonbool integer between 1 and 9')
    totals = {}
    counts = {}
    for era, event, significance in rows:
        if era not in totals:
            totals[era] = 0
            counts[era] = 0
        totals[era] += significance
        counts[era] += 1
    averages = {}
    for era in totals:
        averages[era] = totals[era] // counts[era]
    golden = sorted(era for era in averages if averages[era] >= 7)
    dark = sorted(era for era in averages if averages[era] <= 3)
    zenith = None
    for era in averages:
        if zenith is None or averages[era] > averages[zenith]:
            zenith = era
    return {'total': len(rows),
            'averages': averages,
            'golden': golden,
            'dark': dark,
            'zenith': zenith}
