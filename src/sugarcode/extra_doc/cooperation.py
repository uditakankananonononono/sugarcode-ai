"""Row 768, Cooperation: balancing supplied work hours.

Works together by sharing. Each row pairs a worker name of 1 to 8
characters with an integer hours value from 1 to 8. Reported: the
(worker, total hours) pairs sorted by hours descending with names
breaking ties, the grand total of hours, and balanced - true when
the busiest and quietest workers differ by at most one hour (true
also when there is nobody). Caps (checked before any work): 0 to
100 rows.
NOT_CLAIMED: real teamwork, scheduling, payroll, fairness proofs,
negotiation, productivity, production readiness.
"""
SCOPE = 'PARTIAL: hour balancing over supplied rows, no real cooperation'
NOT_CLAIMED = ('real teamwork', 'scheduling', 'payroll', 'fairness proofs',
               'negotiation', 'productivity', 'production readiness')

MAX_ROWS = 100
MAX_WORKER = 8
MAX_HOURS = 8


def share(rows_in):
    if type(rows_in) not in (list, tuple):
        raise TypeError('shifts must be a list or tuple')
    if len(rows_in) > MAX_ROWS:
        raise ValueError('shifts must contain at most 100 rows')
    rows = []
    for row in rows_in:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each shift must be a (worker, hours) row')
        worker, hours = row
        if type(worker) is not str or not 1 <= len(worker) <= MAX_WORKER:
            raise ValueError('worker must be a string of 1 to 8 characters')
        if type(hours) is not int or not 1 <= hours <= MAX_HOURS:
            raise ValueError('hours must be an integer from 1 to 8')
        rows.append((worker, hours))
    totals = {}
    for worker, hours in rows:
        totals[worker] = totals.get(worker, 0) + hours
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    values = list(totals.values())
    balanced = not values or max(values) - min(values) <= 1
    return {'hours': ranked, 'total': sum(values), 'balanced': balanced}
