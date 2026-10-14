"""Row 654, At-Least-Once Semantics: resend until acknowledged.

at_least_once_delivery takes ack_outcomes, a list or tuple of 0 to 10 real
bools, one per send attempt of a single message: True when the sender saw
the acknowledgement for that attempt, False when it was lost. Every attempt
reaches the receiver. max_attempts is a nonbool int from 1 to 10 (default
3). The sender resends until an acknowledgement is seen or max_attempts
attempts were made. Reported: status ('acked' when an acknowledgement was
seen, 'gave_up' when max_attempts attempts passed with none, 'pending' when
the outcomes ran out first), attempts (made), copies (received by the
receiver, equal to attempts) and duplicates (copies beyond the first, 0 for
no attempt). Outcomes after the stopping attempt are validated but unused.
Checks, in this order: ack_outcomes type, size, max_attempts, then each
outcome.
NOT_CLAIMED: real networks, timers, ordering, persistence, receiver
deduplication, production readiness.
"""
SCOPE = 'PARTIAL: resend-until-acked simulation over supplied outcomes, no real network'
NOT_CLAIMED = ('real networks', 'timers', 'ordering', 'persistence', 'receiver deduplication',
               'production readiness')

MAX_OUTCOMES = 10


def at_least_once_delivery(ack_outcomes, max_attempts=3):
    if type(ack_outcomes) not in (list, tuple):
        raise TypeError('ack_outcomes must be a list or tuple')
    if len(ack_outcomes) > MAX_OUTCOMES:
        raise ValueError('ack_outcomes must contain at most 10 entries')
    if type(max_attempts) is not int or not 1 <= max_attempts <= 10:
        raise ValueError('max_attempts must be a nonbool integer between 1 and 10')
    for o in ack_outcomes:
        if type(o) is not bool:
            raise ValueError('each outcome must be a bool')
    attempts = 0
    status = 'pending'
    for o in ack_outcomes:
        attempts += 1
        if o:
            status = 'acked'
            break
        if attempts == max_attempts:
            status = 'gave_up'
            break
    return {'status': status, 'attempts': attempts, 'copies': attempts,
            'duplicates': max(attempts - 1, 0)}
