"""Row 1953, Title: Trustworthy AI

count_silvers(rows): rows are (system, trial, score)
triples; system and trial strings of 1 to 16
characters; score a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each system its
silvers (trials where its score is the highest score
strictly below the trial's top score), the total
silvers, the outright trials (a single system alone
at the top), and the leader (the most silvers, first
supplied on ties, or None when no trial has a
silver).

SCOPE: PARTIAL: silver counting over supplied scores
NOT_CLAIMED: trial design, score calibration,
red-teaming, certification, production readiness.
"""

SCOPE = 'PARTIAL: silver counting over supplied scores'
NOT_CLAIMED = ('trial design', 'score calibration',
               'red-teaming', 'certification',
               'production readiness')


def count_silvers(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (system, trial, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        system, trial, score = row
        if type(system) is not str or not 1 <= len(system) <= 16:
            raise ValueError(f'row {i}: system must be a string of 1 to 16 characters')
        if type(trial) is not str or not 1 <= len(trial) <= 16:
            raise ValueError(f'row {i}: trial must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    per_trial = {}
    order = {}
    for system, trial, score in rows:
        if trial not in per_trial:
            per_trial[trial] = {}
        if system not in order:
            order[system] = True
        if system not in per_trial[trial] or score > per_trial[trial][system]:
            per_trial[trial][system] = score
    silvers = {}
    total = 0
    outright = 0
    for trial in per_trial:
        holders = per_trial[trial]
        top = max(holders.values())
        tops = 0
        rest = []
        for system in holders:
            if holders[system] == top:
                tops += 1
            else:
                rest.append(holders[system])
        if tops == 1:
            outright += 1
        if rest:
            silver = max(rest)
            for system in holders:
                if holders[system] == silver:
                    if system not in silvers:
                        silvers[system] = 0
                    silvers[system] += 1
                    total += 1
    leader = None
    for system in order:
        if system not in silvers:
            continue
        if leader is None or silvers[system] > silvers[leader]:
            leader = system
    return {'total': len(rows),
            'silvers': silvers,
            'count': total,
            'outright': outright,
            'leader': leader}
