"""Row 636, Error Budgets: budget arithmetic for a request count.

budget_status takes the
request count (1 to 1000000), the failed count (0 to total), an SLO of
1 to 100 percent (default 99) and a freeze gate of 1 to 100 percent (default 80). The allowed failures
are the total times the allowed share of 100 percent, rounded down. Reported: allowed,
remaining (allowed - failed, may be negative), exhausted (failed > allowed),
burn_permille (failures per 1000 of allowed, None when allowed is 0) and freeze
(some failure happened and failures reach the gate share of allowed).
Caps (checked before any work): nonbool ints in the ranges above.
NOT_CLAIMED: measuring real traffic, time windows, burn rate alerting,
release tooling, org policy, production readiness.
"""
SCOPE = 'PARTIAL: error budget arithmetic over supplied counts, no real measurement'
NOT_CLAIMED = ('measuring real traffic', 'time windows', 'burn rate alerting',
               'release tooling', 'org policy', 'production readiness')

MAX_TOTAL = 1000000


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def budget_status(total, failed, slo_percent=99, gate_percent=80):
    _int(total, 1, MAX_TOTAL, 'total must be a nonbool integer between 1 and 1000000')
    _int(failed, 0, MAX_TOTAL, 'failed must be a nonbool integer between 0 and 1000000')
    _int(slo_percent, 1, 100, 'slo_percent must be a nonbool integer between 1 and 100')
    _int(gate_percent, 1, 100, 'gate_percent must be a nonbool integer between 1 and 100')
    if failed > total:
        raise ValueError('failed must not exceed total')
    allowed = total * (100 - slo_percent) // 100
    return {
        'allowed': allowed,
        'remaining': allowed - failed,
        'exhausted': failed > allowed,
        'burn_permille': None if allowed == 0 else failed * 1000 // allowed,
        'freeze': failed > 0 and failed * 100 >= allowed * gate_percent,
    }
