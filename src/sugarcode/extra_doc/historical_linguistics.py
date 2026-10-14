"""Row 1891, Title: Historical Linguistics

trace_shifts(rows): rows are (word, stage, score) triples; word
and stage strings of 1 to 16 characters; score a nonbool
integer between 1 and 9. Caps (checked before any work): 1 to
60 rows. Reported: the total row count, for each word the drift
(its latest supplied score minus its first supplied score), the
risen words (a drift of at least 3, sorted alphabetically), the
fallen words (a drift of at most -3, sorted alphabetically),
and the most volatile word (the largest absolute drift, first
supplied on ties).

SCOPE: PARTIAL: shift tracing over supplied scores
NOT_CLAIMED: sound laws, reconstruction, cognate judgment,
language change, production readiness.
"""

SCOPE = 'PARTIAL: shift tracing over supplied scores'
NOT_CLAIMED = ('sound laws', 'reconstruction', 'cognate judgment',
               'language change', 'production readiness')


def trace_shifts(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (word, stage, score) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        word, stage, score = row
        if type(word) is not str or not 1 <= len(word) <= 16:
            raise ValueError(f'row {i}: word must be a string of 1 to 16 characters')
        if type(stage) is not str or not 1 <= len(stage) <= 16:
            raise ValueError(f'row {i}: stage must be a string of 1 to 16 characters')
        if type(score) is not int or not 1 <= score <= 9:
            raise ValueError(f'row {i}: score must be a nonbool integer between 1 and 9')
    first = {}
    latest = {}
    for word, stage, score in rows:
        if word not in first:
            first[word] = score
        latest[word] = score
    drift = {}
    for word in first:
        drift[word] = latest[word] - first[word]
    risen = sorted(word for word in drift if drift[word] >= 3)
    fallen = sorted(word for word in drift if drift[word] <= -3)
    volatile = None
    for word in drift:
        if volatile is None or abs(drift[word]) > abs(drift[volatile]):
            volatile = word
    return {'total': len(rows),
            'drift': drift,
            'risen': risen,
            'fallen': fallen,
            'volatile': volatile}
