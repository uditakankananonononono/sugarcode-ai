"""Row 770: Teamwork - Functions in groups.

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


def review_task_handoffs(rows):
    """Rows: (task_id, owner_id, completion_bit, handoff_acknowledged_bit).
    Group supplied task status by owner; flag completed unacknowledged handoffs.
    No actual teamwork/coordination execution or independently verified progress.
    """
    _rows(rows, 4)
    for task,owner,complete,ack in rows:
        _label(task)
        _label(owner)
        _integer(complete, 0, 1)
        _integer(ack, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate task')
    owners=[]
    for owner in sorted({x[1] for x in rows}):
        assigned=[x for x in rows if x[1]==owner]
        owners.append((owner,len(assigned),sum(x[2] for x in assigned)))
    pending=sorted(task for task,_,complete,ack in rows if complete==1 and ack==0)
    return {'owners':owners,'unacknowledged_completed_handoffs':pending}
