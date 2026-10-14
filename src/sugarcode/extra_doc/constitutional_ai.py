"""Row 1945, Title: Constitutional AI

audit_principles(rows): rows are (principle, clause,
severity) triples; principle and clause strings of 1 to
16 characters; severity a nonbool integer between 1 and
9. Caps (checked before any work): 1 to 60 rows.
Reported: the total row count, the peaks (for each
principle, for each clause, its highest severity), the
weakest clause of each principle (the lowest peak,
first supplied on ties), and the exposed principle
(the lowest weakest-peak value, first supplied on
ties).

SCOPE: PARTIAL: peak auditing over supplied severities
NOT_CLAIMED: principle authoring, critique generation,
value learning, red teaming, production readiness.
"""

SCOPE = 'PARTIAL: peak auditing over supplied severities'
NOT_CLAIMED = ('principle authoring', 'critique generation',
               'value learning', 'red teaming',
               'production readiness')


def audit_principles(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (principle, clause, severity) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        principle, clause, severity = row
        if type(principle) is not str or not 1 <= len(principle) <= 16:
            raise ValueError(f'row {i}: principle must be a string of 1 to 16 characters')
        if type(clause) is not str or not 1 <= len(clause) <= 16:
            raise ValueError(f'row {i}: clause must be a string of 1 to 16 characters')
        if type(severity) is not int or not 1 <= severity <= 9:
            raise ValueError(f'row {i}: severity must be a nonbool integer between 1 and 9')
    peaks = {}
    for principle, clause, severity in rows:
        if principle not in peaks:
            peaks[principle] = {}
        if clause not in peaks[principle] or severity > peaks[principle][clause]:
            peaks[principle][clause] = severity
    weakest = {}
    for principle in peaks:
        chosen = None
        for clause in peaks[principle]:
            if chosen is None or peaks[principle][clause] < peaks[principle][chosen]:
                chosen = clause
        weakest[principle] = chosen
    exposed = None
    for principle in weakest:
        if (exposed is None
                or peaks[principle][weakest[principle]]
                < peaks[exposed][weakest[exposed]]):
            exposed = principle
    return {'total': len(rows),
            'peaks': peaks,
            'weakest': weakest,
            'exposed': exposed}
