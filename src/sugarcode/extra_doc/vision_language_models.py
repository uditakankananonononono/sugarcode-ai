"""Row 1926, Title: Vision-Language Models

count_solos(rows): rows are (caption, model, score)
triples; caption and model strings of 1 to 16 characters;
score a nonbool integer between 1 and 9. Caps (checked
before any work): 1 to 60 rows. Reported: the total row
count, for each model its solo wins (captions where it
alone holds the best score), the tied captions (a best
score shared by at least 2 models, sorted
alphabetically), and the leader (the most solo wins,
first supplied on ties).

SCOPE: PARTIAL: solo counting over supplied scores
NOT_CLAIMED: image encoding, tokenization, benchmark
design, safety filtering, production readiness.
"""

SCOPE = 'PARTIAL: solo counting over supplied scores'
NOT_CLAIMED = ('image encoding', 'tokenization', 'benchmark design',
               'safety filtering', 'production readiness')


def count_solos(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (caption, model, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        caption, model, score = row
        if type(caption) is not str or not 1 <= len(caption) <= 16:
            raise ValueError(f'row {i}: caption must be a string of 1 to 16 characters')
        if type(model) is not str or not 1 <= len(model) <= 16:
            raise ValueError(f'row {i}: model must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    best = {}
    holders = {}
    order = {}
    for caption, model, score in rows:
        if model not in order:
            order[model] = True
        if caption not in best or score > best[caption]:
            best[caption] = score
            holders[caption] = {model: True}
        elif score == best[caption]:
            holders[caption][model] = True
    wins = {}
    tied = []
    for caption in holders:
        if len(holders[caption]) == 1:
            for model in holders[caption]:
                if model not in wins:
                    wins[model] = 0
                wins[model] += 1
        else:
            tied.append(caption)
    leader = None
    for model in order:
        if model not in wins:
            continue
        if leader is None or wins[model] > wins[leader]:
            leader = model
    return {'total': len(rows),
            'wins': wins,
            'tied': sorted(tied),
            'leader': leader}
