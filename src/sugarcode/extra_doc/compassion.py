"""Row 765, Compassion: ordering supplied cases by severity.

Responds to suffering by triage. Each row pairs a case name of 1 to
8 characters with an integer severity from 1 to 5, and each case
appears at most once. Reported: the cases ordered by severity
descending with names breaking ties, how many cases are critical
(severity 4 or 5), and the case total. Caps (checked before any
work): 0 to 100 rows.
NOT_CLAIMED: real triage, medicine, emergency response, counseling,
suffering measurement, prioritization policy, production readiness.
"""
SCOPE = 'PARTIAL: severity ordering over supplied cases, no real compassion'
NOT_CLAIMED = ('real triage', 'medicine', 'emergency response', 'counseling',
               'suffering measurement', 'prioritization policy',
               'production readiness')

MAX_ROWS = 100
MAX_CASE = 8
MAX_SEVERITY = 5


def triage(cases):
    if type(cases) not in (list, tuple):
        raise TypeError('cases must be a list or tuple')
    if len(cases) > MAX_ROWS:
        raise ValueError('cases must contain at most 100 rows')
    rows = []
    for row in cases:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each case must be a (case, severity) row')
        case, severity = row
        if type(case) is not str or not 1 <= len(case) <= MAX_CASE:
            raise ValueError('case must be a string of 1 to 8 characters')
        if type(severity) is not int or not 1 <= severity <= MAX_SEVERITY:
            raise ValueError('severity must be an integer from 1 to 5')
        rows.append((case, severity))
    seen = set()
    for case, severity in rows:
        if case in seen:
            raise ValueError('each case may appear only once')
        seen.add(case)
    order = [case for case, severity in sorted(rows, key=lambda kv: (-kv[1], kv[0]))]
    critical = sum(1 for case, severity in rows if severity >= 4)
    return {'order': order, 'critical': critical, 'total': len(rows)}
