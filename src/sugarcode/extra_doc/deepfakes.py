"""Row 1933, Title: Deepfakes

anchor_counts(rows): rows are (frame, model, score)
triples; frame and model strings of 1 to 16
characters; score a nonbool integer between 1 and 9.
Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, for each model the
anchor count (how many of its scores equal its own
first supplied score), the steady models (every
score equal to the debut, sorted alphabetically),
and the firmest model (the largest anchor count,
first supplied on ties).

SCOPE: PARTIAL: debut-anchor counting over supplied rows
NOT_CLAIMED: face-swap fidelity, lip-sync accuracy,
detection evasion, consent compliance, production
readiness.
"""

SCOPE = 'PARTIAL: debut-anchor counting over supplied rows'
NOT_CLAIMED = ('face-swap fidelity', 'lip-sync accuracy',
               'detection evasion', 'consent compliance',
               'production readiness')


def anchor_counts(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (frame, model, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        frame, model, score = row
        if type(frame) is not str or not 1 <= len(frame) <= 16:
            raise ValueError(f'row {i}: frame must be a string of 1 to 16 characters')
        if type(model) is not str or not 1 <= len(model) <= 16:
            raise ValueError(f'row {i}: model must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    firsts = {}
    anchors = {}
    supplied = {}
    for frame, model, score in rows:
        if model not in firsts:
            firsts[model] = score
            anchors[model] = 0
            supplied[model] = 0
        supplied[model] += 1
        if score == firsts[model]:
            anchors[model] += 1
    steady = sorted(m for m in anchors if anchors[m] == supplied[m])
    firmest = None
    for model in anchors:
        if firmest is None or anchors[model] > anchors[firmest]:
            firmest = model
    return {'total': len(rows),
            'anchors': anchors,
            'steady': steady,
            'firmest': firmest}
