"""Row 656, Retry Logic: retry decisions over supplied attempt outcomes.

retry_attempts takes outcomes, a list or tuple of 0 to 12 strings, one per
attempt: 'ok', 'transient' or 'fatal'. max_retries is a nonbool int from 0
to 10 (default 3), so at most max_retries + 1 attempts are made. 'ok' stops
with success. 'fatal' stops at once with no retry. 'transient' is retried
while retries remain. Reported: status ('success', 'fatal', 'exhausted' when
the last allowed attempt was transient, 'pending' when the outcomes ran out
first), attempts (made) and retries (attempts after the first, 0 for none).
Outcomes after the stopping attempt are validated but unused.
Checks, in this order: outcomes type, size, max_retries, then each outcome.
NOT_CLAIMED: real calls, timers, backoff delays, jitter, circuit breaking,
production readiness.
"""
SCOPE = 'PARTIAL: retry decisions over supplied attempt outcomes, no real calls'
NOT_CLAIMED = ('real calls', 'timers', 'backoff delays', 'jitter', 'circuit breaking',
               'production readiness')

KINDS = ('ok', 'transient', 'fatal')
MAX_OUTCOMES = 12


def retry_attempts(outcomes, max_retries=3):
    if type(outcomes) not in (list, tuple):
        raise TypeError('outcomes must be a list or tuple')
    if len(outcomes) > MAX_OUTCOMES:
        raise ValueError('outcomes must contain at most 12 entries')
    if type(max_retries) is not int or not 0 <= max_retries <= 10:
        raise ValueError('max_retries must be a nonbool integer between 0 and 10')
    for o in outcomes:
        if type(o) is not str or o not in KINDS:
            raise ValueError('outcome must be ok, transient or fatal')
    attempts = 0
    status = 'pending'
    for o in outcomes:
        attempts += 1
        if o == 'ok':
            status = 'success'
            break
        if o == 'fatal':
            status = 'fatal'
            break
        if attempts == max_retries + 1:
            status = 'exhausted'
            break
    return {'status': status, 'attempts': attempts, 'retries': max(attempts - 1, 0)}
