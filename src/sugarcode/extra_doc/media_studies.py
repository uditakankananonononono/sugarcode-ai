"""Row 1913, Title: Media Studies

map_stories(rows): rows are (story, outlet, reach) triples;
story and outlet strings of 1 to 16 characters; reach a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for
each story the number of distinct outlets carrying it,
the syndicated stories (carried by at least 2 outlets,
sorted alphabetically), the exclusive outlets (the sole
carrier of at least one story, sorted alphabetically),
and for each syndicated story its lead outlet (the
largest reach among its rows, first supplied on ties).

SCOPE: PARTIAL: story mapping over supplied reaches
NOT_CLAIMED: journalism ethics, audience measurement,
advertising, media law, production readiness.
"""

SCOPE = 'PARTIAL: story mapping over supplied reaches'
NOT_CLAIMED = ('journalism ethics', 'audience measurement',
               'advertising', 'media law', 'production readiness')


def map_stories(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (story, outlet, reach) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        story, outlet, reach = row
        if type(story) is not str or not 1 <= len(story) <= 16:
            raise ValueError(f'row {i}: story must be a string of 1 to 16 characters')
        if type(outlet) is not str or not 1 <= len(outlet) <= 16:
            raise ValueError(f'row {i}: outlet must be a string of 1 to 16 characters')
        if type(reach) is not int or not 1 <= reach <= 9:
            raise ValueError(f'row {i}: reach must be a nonbool integer between 1 and 9')
    carriers = {}
    leads = {}
    for story, outlet, reach in rows:
        if story not in carriers:
            carriers[story] = {}
        if outlet not in carriers[story] or reach > carriers[story][outlet]:
            carriers[story][outlet] = reach
        if story in leads:
            if reach > carriers[story][leads[story]]:
                leads[story] = outlet
        else:
            leads[story] = outlet
    counts = {}
    for story in carriers:
        counts[story] = len(carriers[story])
    syndicated = sorted(s for s in counts if counts[s] >= 2)
    exclusive = set()
    for story in carriers:
        if counts[story] == 1:
            for outlet in carriers[story]:
                exclusive.add(outlet)
    out_leads = {}
    for story in syndicated:
        out_leads[story] = leads[story]
    return {'total': len(rows),
            'carriers': counts,
            'syndicated': syndicated,
            'exclusive': sorted(exclusive),
            'leads': out_leads}
