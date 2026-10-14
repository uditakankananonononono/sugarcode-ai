"""Row 1952, Title: Responsible AI

track_debuts(rows): rows are (policy, team, score)
triples; policy and team strings of 1 to 16
characters; score a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each policy the
number of teams whose first scored policy it is, the
favorite debut policy (the most teams, first supplied
on ties), and the solo teams (whose debut policy no
other team debuted with, sorted alphabetically).

SCOPE: PARTIAL: debut tracking over supplied scores
NOT_CLAIMED: policy authoring, compliance mapping,
risk assessment, incident review, production
readiness.
"""

SCOPE = 'PARTIAL: debut tracking over supplied scores'
NOT_CLAIMED = ('policy authoring', 'compliance mapping',
               'risk assessment', 'incident review',
               'production readiness')


def track_debuts(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (policy, team, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        policy, team, score = row
        if type(policy) is not str or not 1 <= len(policy) <= 16:
            raise ValueError(f'row {i}: policy must be a string of 1 to 16 characters')
        if type(team) is not str or not 1 <= len(team) <= 16:
            raise ValueError(f'row {i}: team must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    first = {}
    order = {}
    for policy, team, score in rows:
        if team not in first:
            first[team] = policy
        if policy not in order:
            order[policy] = True
    debuts = {}
    holder = {}
    for team in first:
        policy = first[team]
        if policy not in debuts:
            debuts[policy] = 0
            holder[policy] = []
        debuts[policy] += 1
        holder[policy].append(team)
    favorite = None
    for policy in order:
        if policy in debuts and (favorite is None
                                 or debuts[policy] > debuts[favorite]):
            favorite = policy
    solo = []
    for team in first:
        if debuts[first[team]] == 1:
            solo.append(team)
    return {'total': len(rows),
            'debuts': debuts,
            'favorite': favorite,
            'solo': sorted(solo)}
