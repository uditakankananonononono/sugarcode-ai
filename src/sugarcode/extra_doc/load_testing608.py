"""Row 608: Load Testing - Tests under stress.

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


def simulate_load(rows):
    """Rows: (request_id, arrival_time, service_duration). Simulate FCFS
    single-server load sorted arrival then ID. Return queue waits/finishes and
    exact average wait; no actual service stress, throughput measurement or
    concurrency/network claim. Supplied times, no sleep or external calls.
    """
    _rows(rows, 3)
    for request, arrival, duration in rows:
        _label(request)
        _integer(arrival, 0, 1000000)
        _integer(duration, 1, 1000000)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate request')
    clock=0
    trace=[]
    for request,arrival,duration in sorted(rows,key=lambda x:(x[1],x[0])):
        start=max(clock,arrival)
        finish=start+duration
        trace.append((request,arrival,start,finish,start-arrival))
        clock=finish
    from fractions import Fraction as F
    waits=[x[4] for x in trace]
    return {'requests':trace,'mean_wait_fraction':str(F(sum(waits),len(waits))),
            'maximum_wait':max(waits),'finish':clock}
