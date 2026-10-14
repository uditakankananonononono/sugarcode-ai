"""Row 1954, Title: AI Governance

count_covers(rows): rows are (framework, region,
level) triples; framework and region strings of 1 to
16 characters; level a nonbool integer between 1
and 9. Caps (checked before any work): 1 to 60
rows. Reported: the total row count, for each
framework the number of other frameworks whose
region set is strictly inside its own, the total
covers, the independent frameworks (covering none
and covered by none, sorted alphabetically), and
the leader (the most covers, first supplied on
ties, or None when no framework covers another).

SCOPE: PARTIAL: cover counting over supplied levels
NOT_CLAIMED: framework drafting, jurisdiction
mapping, enforcement modeling, treaty analysis,
production readiness.
"""

SCOPE = 'PARTIAL: cover counting over supplied levels'
NOT_CLAIMED = ('framework drafting', 'jurisdiction mapping',
               'enforcement modeling', 'treaty analysis',
               'production readiness')


def count_covers(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (framework, region, level) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        framework, region, level = row
        if type(framework) is not str or not 1 <= len(framework) <= 16:
            raise ValueError(f'row {i}: framework must be a string of 1 to 16 characters')
        if type(region) is not str or not 1 <= len(region) <= 16:
            raise ValueError(f'row {i}: region must be a string of 1 to 16 characters')
        if type(level) is not int or not 1 <= level <= 9:
            raise ValueError(f'row {i}: level must be a nonbool integer between 1 and 9')
    regions = {}
    order = {}
    for framework, region, level in rows:
        if framework not in regions:
            regions[framework] = {}
            order[framework] = True
        regions[framework][region] = True
    covers = {}
    covered = {}
    total = 0
    for framework in regions:
        for other in regions:
            if other == framework:
                continue
            inside = True
            for region in regions[other]:
                if region not in regions[framework]:
                    inside = False
            if inside and len(regions[other]) < len(regions[framework]):
                if framework not in covers:
                    covers[framework] = 0
                covers[framework] += 1
                covered[other] = True
                total += 1
    independent = []
    for framework in regions:
        if framework not in covers and framework not in covered:
            independent.append(framework)
    leader = None
    for framework in order:
        if framework not in covers:
            continue
        if leader is None or covers[framework] > covers[leader]:
            leader = framework
    return {'total': len(rows),
            'covers': covers,
            'count': total,
            'independent': sorted(independent),
            'leader': leader}
