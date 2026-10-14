"""Row 1924, Title: Large Language Models

weigh_deficits(rows): rows are (prompt, model, score)
triples; prompt and model strings of 1 to 16 characters;
score a nonbool integer between 1 and 9. Caps (checked
before any work): 1 to 60 rows. Reported: the total row
count, for each model its deficit (the sum over its rows
of how far the score sits below that prompt's best
score), the off-peak models (any deficit at all, sorted
alphabetically), and the sharpest model (the smallest
deficit, first supplied on ties).

SCOPE: PARTIAL: deficit weighing over supplied scores
NOT_CLAIMED: training, alignment, evaluation design,
deployment safety, production readiness.
"""

SCOPE = 'PARTIAL: deficit weighing over supplied scores'
NOT_CLAIMED = ('training', 'alignment', 'evaluation design',
               'deployment safety', 'production readiness')


def weigh_deficits(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (prompt, model, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        prompt, model, score = row
        if type(prompt) is not str or not 1 <= len(prompt) <= 16:
            raise ValueError(f'row {i}: prompt must be a string of 1 to 16 characters')
        if type(model) is not str or not 1 <= len(model) <= 16:
            raise ValueError(f'row {i}: model must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    prompt_max = {}
    for prompt, model, score in rows:
        if prompt not in prompt_max or score > prompt_max[prompt]:
            prompt_max[prompt] = score
    deficits = {}
    for prompt, model, score in rows:
        if model not in deficits:
            deficits[model] = 0
        deficits[model] += prompt_max[prompt] - score
    off_peak = sorted(m for m in deficits if deficits[m] > 0)
    sharpest = None
    for model in deficits:
        if sharpest is None or deficits[model] < deficits[sharpest]:
            sharpest = model
    return {'total': len(rows),
            'deficits': deficits,
            'off_peak': off_peak,
            'sharpest': sharpest}
