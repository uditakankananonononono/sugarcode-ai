"""Row 620: Throttling - Limits usage.

SCOPED planning aid over caller supplied rows. No external actions, persistence,
capability development evidence, organization quality, or optimal policy claim.
Explicit import only; 1..32 tuple rows. Labels are lowercase ASCII identifiers.
"""
import re

LABEL = re.compile(r"[a-z][a-z0-9_]{0,23}\Z")


def _label(value):
    if type(value) is not str:
        raise TypeError('exact string label required')
    if len(value) > 24 or LABEL.fullmatch(value) is None:
        raise ValueError('label must be 1..24 lowercase identifier characters')


def _integer(value, low, high):
    if type(value) is not int:
        raise TypeError('exact nonbool integer required')
    if not low <= value <= high:
        raise ValueError('integer outside declared range')


def _rows(rows, arity):
    if type(rows) is not list:
        raise TypeError('exact list required')
    if not 1 <= len(rows) <= 32:
        raise ValueError('row count must be 1..32')
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple row required')
        if len(row) != arity:
            raise ValueError('wrong row arity')


def simulate_token_bucket(rows):
    """Rows: (request_id, integer_time, unit_cost). Fixed token bucket,
    initially 10 tokens at time0, refill2/timeunit, capped10. Chronological
    time then ID ordering; rejected requests consume no tokens. Local simulator
    only, no clock/network/request enforcement or persistent rate limiting.
    """
    _rows(rows, 3)
    for request, timestamp, cost in rows:
        _label(request)
        _integer(timestamp, 0, 1000000)
        _integer(cost, 1, 10)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate request')
    tokens=10
    previous=0
    trace=[]
    for request,timestamp,cost in sorted(rows,key=lambda x:(x[1],x[0])):
        tokens=min(10,tokens+2*(timestamp-previous))
        accepted=cost<=tokens
        if accepted:
            tokens-=cost
        trace.append((request,timestamp,accepted,tokens))
        previous=timestamp
    return {'requests':trace,'remaining_tokens':tokens,'accepted_count':sum(x[2] for x in trace)}
