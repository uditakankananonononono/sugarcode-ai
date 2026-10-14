"""Row 1949, Title: Explainable AI

track_tops(rows): rows are (feature, model, weight)
triples; feature and model strings of 1 to 16
characters; weight a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each model its
displacements (rows after which the model's top
feature, the highest accumulated weight, first
supplied on ties, differs from before the row), the
final top feature of each model, and the leader (the
most displacements, first supplied on ties, or None
when no model is displaced).

SCOPE: PARTIAL: top tracking over supplied weights
NOT_CLAIMED: feature extraction, saliency methods,
counterfactual generation, model debugging, production
readiness.
"""

SCOPE = 'PARTIAL: top tracking over supplied weights'
NOT_CLAIMED = ('feature extraction', 'saliency methods',
               'counterfactual generation', 'model debugging',
               'production readiness')


def track_tops(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (feature, model, weight) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        feature, model, weight = row
        if type(feature) is not str or not 1 <= len(feature) <= 16:
            raise ValueError(f'row {i}: feature must be a string of 1 to 16 characters')
        if type(model) is not str or not 1 <= len(model) <= 16:
            raise ValueError(f'row {i}: model must be a string of 1 to 16 characters')
        if type(weight) is not int or not 1 <= weight <= 9:
            raise ValueError(f'row {i}: weight must be a nonbool integer between 1 and 9')
    sums = {}
    order = {}
    displacements = {}
    tops = {}
    for feature, model, weight in rows:
        if model not in order:
            order[model] = True
        if model not in sums:
            sums[model] = {}
        if feature not in sums[model]:
            sums[model][feature] = 0
        sums[model][feature] += weight
        top = None
        for name in sums[model]:
            if top is None or sums[model][name] > sums[model][top]:
                top = name
        if model in tops and tops[model] != top:
            if model not in displacements:
                displacements[model] = 0
            displacements[model] += 1
        tops[model] = top
    leader = None
    for model in order:
        if model not in displacements:
            continue
        if leader is None or displacements[model] > displacements[leader]:
            leader = model
    return {'total': len(rows),
            'displacements': displacements,
            'tops': tops,
            'leader': leader}
