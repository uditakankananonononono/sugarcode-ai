"""Row 1895, Title: Translation Studies

assess_translations(rows): rows are (passage, translator,
fidelity) triples; passage and translator strings of 1 to 16
characters; fidelity a nonbool integer between 1 and 9. Caps
(checked before any work): 1 to 60 rows. Reported: the total
row count, for each passage the number of translations, the
consensus passages (at least 2 translations that all agree,
sorted alphabetically), the disputed passages (fidelity spread
of at least 6, sorted alphabetically), and the polarizing
passage (the largest spread, first supplied on ties).

SCOPE: PARTIAL: translation assessment over supplied fidelities
NOT_CLAIMED: translation quality judgment, fluency measurement,
adequacy testing, machine translation, production readiness.
"""

SCOPE = 'PARTIAL: translation assessment over supplied fidelities'
NOT_CLAIMED = ('translation quality judgment', 'fluency measurement',
               'adequacy testing', 'machine translation',
               'production readiness')


def assess_translations(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (passage, translator, fidelity) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        passage, translator, fidelity = row
        if type(passage) is not str or not 1 <= len(passage) <= 16:
            raise ValueError(f'row {i}: passage must be a string of 1 to 16 characters')
        if type(translator) is not str or not 1 <= len(translator) <= 16:
            raise ValueError(f'row {i}: translator must be a string of 1 to 16 characters')
        if type(fidelity) is not int or not 1 <= fidelity <= 9:
            raise ValueError(f'row {i}: fidelity must be a nonbool integer between 1 and 9')
    counts = {}
    low = {}
    high = {}
    for passage, translator, fidelity in rows:
        if passage not in counts:
            counts[passage] = 0
            low[passage] = fidelity
            high[passage] = fidelity
        counts[passage] += 1
        if fidelity < low[passage]:
            low[passage] = fidelity
        if fidelity > high[passage]:
            high[passage] = fidelity
    consensus = sorted(p for p in counts if counts[p] >= 2 and high[p] == low[p])
    disputed = sorted(p for p in counts if high[p] - low[p] >= 6)
    polarizing = None
    for p in counts:
        if polarizing is None or high[p] - low[p] > high[polarizing] - low[polarizing]:
            polarizing = p
    return {'total': len(rows),
            'counts': counts,
            'consensus': consensus,
            'disputed': disputed,
            'polarizing': polarizing}
