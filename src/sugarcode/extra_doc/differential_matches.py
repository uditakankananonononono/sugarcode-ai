"""Row 1117, Differential Diagnosis Generation.

differential_matches uses only caller-supplied candidate labels and support
x/conflict y counts. Score=x-conflict_cost*y. Rank higher score first, smaller
total evidence count x+y next, then label. Returns ranked as (label,score,
total_count), ties as all labels sharing the top score in rank order,
all_conflicted as whether every candidate has a positive conflict count.
This does not create medical diagnoses or establish clinical probabilities.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
conflict_cost defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, conflict_cost, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: medical diagnosis, clinical likelihood, candidate completeness, evidence validity, production readiness.
"""

SCOPE = 'PARTIAL: ranks caller-named candidates by supplied supporting and conflicting counts, no diagnosis is generated'
NOT_CLAIMED = ('medical diagnosis', 'clinical likelihood', 'candidate completeness', 'evidence validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def differential_matches(rows, conflict_cost=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(conflict_cost) is not int or not 1 <= conflict_cost <= 5:
        raise ValueError('conflict_cost must be a nonbool integer between 1 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 0 and 100')
        if type(y) is not int or not 0 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 0 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    ranked = [(n, support - conflict_cost * conflict, support + conflict) for n, support, conflict in clean]
    ranked.sort(key=lambda r: (-r[1], r[2], r[0]))
    return {'ranked': ranked, 'ties': [n for n, score, count in ranked if score == ranked[0][1]],
            'all_conflicted': all(conflict > 0 for n, support, conflict in clean)}
