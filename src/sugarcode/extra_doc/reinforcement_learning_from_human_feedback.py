"""Row 1944, Title: Reinforcement Learning from Human Feedback

weight_feedback(rows): rows are (prompt, labeler, score)
triples; prompt and labeler strings of 1 to 16
characters; score a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each labeler its
weighted score (each score multiplied by its position
among that labeler's rows, earliest position 1), the
grand weighted total, and the leading labeler (the
highest weighted score, first supplied on ties).

SCOPE: PARTIAL: weighting over supplied scores
NOT_CLAIMED: reward model training, policy optimization,
kl regularization, human rater screening, production
readiness.
"""

SCOPE = 'PARTIAL: weighting over supplied scores'
NOT_CLAIMED = ('reward model training', 'policy optimization',
               'kl regularization', 'human rater screening',
               'production readiness')


def weight_feedback(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (prompt, labeler, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        prompt, labeler, score = row
        if type(prompt) is not str or not 1 <= len(prompt) <= 16:
            raise ValueError(f'row {i}: prompt must be a string of 1 to 16 characters')
        if type(labeler) is not str or not 1 <= len(labeler) <= 16:
            raise ValueError(f'row {i}: labeler must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    seen = {}
    order = {}
    weighted = {}
    for prompt, labeler, score in rows:
        if labeler not in order:
            order[labeler] = True
        if labeler not in seen:
            seen[labeler] = 0
            weighted[labeler] = 0
        seen[labeler] += 1
        weighted[labeler] += score * seen[labeler]
    leader = None
    for labeler in order:
        if leader is None or weighted[labeler] > weighted[leader]:
            leader = labeler
    return {'total': len(rows),
            'weighted': weighted,
            'weight': sum(weighted.values()),
            'leader': leader}
