"""Row 1948, Title: AI Ethics

count_revisits(rows): rows are (dilemma, framework,
weight) triples; dilemma and framework strings of 1 to
16 characters; weight a nonbool integer between 1 and
9. Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each framework its
revisits (rows weighing a dilemma that framework has
already weighed), the revisited dilemmas (at least one
revisit, sorted alphabetically), and the leader (the
most revisits, first supplied on ties, or None when no
framework revisits).

SCOPE: PARTIAL: revisit counting over supplied weights
NOT_CLAIMED: dilemma curation, framework comparison,
moral reasoning, stakeholder input, production
readiness.
"""

SCOPE = 'PARTIAL: revisit counting over supplied weights'
NOT_CLAIMED = ('dilemma curation', 'framework comparison',
               'moral reasoning', 'stakeholder input',
               'production readiness')


def count_revisits(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (dilemma, framework, weight) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        dilemma, framework, weight = row
        if type(dilemma) is not str or not 1 <= len(dilemma) <= 16:
            raise ValueError(f'row {i}: dilemma must be a string of 1 to 16 characters')
        if type(framework) is not str or not 1 <= len(framework) <= 16:
            raise ValueError(f'row {i}: framework must be a string of 1 to 16 characters')
        if type(weight) is not int or not 1 <= weight <= 9:
            raise ValueError(f'row {i}: weight must be a nonbool integer between 1 and 9')
    seen = {}
    order = {}
    revisits = {}
    revisited = {}
    for dilemma, framework, weight in rows:
        if framework not in order:
            order[framework] = True
        key = (dilemma, framework)
        if key in seen:
            if framework not in revisits:
                revisits[framework] = 0
            revisits[framework] += 1
            revisited[dilemma] = True
        seen[key] = True
    leader = None
    for framework in order:
        if framework not in revisits:
            continue
        if leader is None or revisits[framework] > revisits[leader]:
            leader = framework
    return {'total': len(rows),
            'revisits': revisits,
            'revisited': sorted(revisited),
            'leader': leader}
