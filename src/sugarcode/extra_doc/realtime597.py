"""Row 597: Real-Time Systems - Meets deadlines.

Bounded planning aid over caller supplied rows. No external actions, persistence,
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


def schedule_jobs(rows):
    """Rows: (job_id, release_time, execution_duration, absolute_deadline).
    Simulate one nonpreemptive processor: among released jobs choose earliest
    deadline then ID, idle until next release if none ready. Return misses.
    Finite simulation only, no optimality, runtime scheduling or hard-real-time
    guarantee. Execution durations and releases are caller declarations.
    """
    _rows(rows, 4)
    for job, release, duration, deadline in rows:
        _label(job)
        _integer(release, 0, 1000000)
        _integer(duration, 1, 1000000)
        _integer(deadline, 0, 1000000)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate job')
    pending=list(rows)
    clock=0
    trace=[]
    while pending:
        ready=[x for x in pending if x[1]<=clock]
        if not ready:
            clock=min(x[1] for x in pending)
            ready=[x for x in pending if x[1]<=clock]
        selected=min(ready,key=lambda x:(x[3],x[0]))
        job,release,duration,deadline=selected
        finish=clock+duration
        trace.append((job,clock,finish,finish>deadline))
        clock=finish
        pending.remove(selected)
    return {'schedule':trace,'missed':[x[0] for x in trace if x[3]],'finish':clock}
