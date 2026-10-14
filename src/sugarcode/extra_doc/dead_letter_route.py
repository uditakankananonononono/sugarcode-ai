"""Row 655, Dead Letter Queue: routing of supplied failed messages.

dead_letter_route takes messages, a list or tuple of 0 to 20 (msg_id, failures)
pairs: msg_id a unique string of 1 to 12 characters, failures a nonbool int
from 0 to 20 (consecutive failures so far). max_failures is a nonbool int from
1 to 20 (default 3). dlq_capacity is a nonbool int from 1 to 10 (default 5).
A message with 0 failures is delivered, with fewer than max_failures it is
retried, otherwise it is dead. Dead messages enter the dead letter queue in
listed order; when it holds more than dlq_capacity, the oldest entries are
dropped. Reported: delivered, retry, dlq (ids, oldest first) and dropped
(ids pushed out, in the order dropped).
Checks, in this order: messages type, size, max_failures, dlq_capacity, then
per message the pair shape, id, duplicate id and failures.
NOT_CLAIMED: real queues, redrive, alerting, retention by time, persistence,
production readiness.
"""
SCOPE = 'PARTIAL: dead letter routing of supplied failure counts, no real queue'
NOT_CLAIMED = ('real queues', 'redrive', 'alerting', 'retention by time', 'persistence',
               'production readiness')

MAX_MESSAGES = 20


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def dead_letter_route(messages, max_failures=3, dlq_capacity=5):
    if type(messages) not in (list, tuple):
        raise TypeError('messages must be a list or tuple')
    if len(messages) > MAX_MESSAGES:
        raise ValueError('messages must contain at most 20 entries')
    _int(max_failures, 1, 20, 'max_failures must be a nonbool integer between 1 and 20')
    _int(dlq_capacity, 1, 10, 'dlq_capacity must be a nonbool integer between 1 and 10')
    seen = set()
    for m in messages:
        if type(m) not in (list, tuple) or len(m) != 2:
            raise ValueError('each message must be a (msg_id, failures) pair')
        mid, failures = m
        if type(mid) is not str or not 1 <= len(mid) <= 12:
            raise ValueError('msg_id must be a string of 1 to 12 characters')
        if mid in seen:
            raise ValueError('duplicate msg_id')
        seen.add(mid)
        _int(failures, 0, 20, 'failures must be a nonbool integer between 0 and 20')
    delivered, retry, dlq, dropped = [], [], [], []
    for mid, failures in messages:
        if failures == 0:
            delivered.append(mid)
        elif failures < max_failures:
            retry.append(mid)
        else:
            dlq.append(mid)
            if len(dlq) > dlq_capacity:
                dropped.append(dlq.pop(0))
    return {'delivered': delivered, 'retry': retry, 'dlq': dlq, 'dropped': dropped}
