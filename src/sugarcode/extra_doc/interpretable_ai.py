"""Row 1950, Title: Interpretable AI

count_slips(rows): rows are (rule, model, gain)
triples; rule and model strings of 1 to 16
characters; gain a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each rule its
slips (rows whose gain is strictly below the rule's
previous gain), the total slips, and the leader (the
most slips, first supplied on ties, or None when no
rule slips).

SCOPE: PARTIAL: slip counting over supplied gains
NOT_CLAIMED: rule extraction, surrogate modeling,
distillation, glossary curation, production readiness.
"""

SCOPE = 'PARTIAL: slip counting over supplied gains'
NOT_CLAIMED = ('rule extraction', 'surrogate modeling',
               'distillation', 'glossary curation',
               'production readiness')


def count_slips(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (rule, model, gain) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        rule, model, gain = row
        if type(rule) is not str or not 1 <= len(rule) <= 16:
            raise ValueError(f'row {i}: rule must be a string of 1 to 16 characters')
        if type(model) is not str or not 1 <= len(model) <= 16:
            raise ValueError(f'row {i}: model must be a string of 1 to 16 characters')
        if type(gain) is not int or not 1 <= gain <= 9:
            raise ValueError(f'row {i}: gain must be a nonbool integer between 1 and 9')
    previous = {}
    order = {}
    slips = {}
    total = 0
    for rule, model, gain in rows:
        if rule not in order:
            order[rule] = True
        if rule in previous and gain < previous[rule]:
            if rule not in slips:
                slips[rule] = 0
            slips[rule] += 1
            total += 1
        previous[rule] = gain
    leader = None
    for rule in order:
        if rule not in slips:
            continue
        if leader is None or slips[rule] > slips[leader]:
            leader = rule
    return {'total': len(rows),
            'slips': slips,
            'count': total,
            'leader': leader}
