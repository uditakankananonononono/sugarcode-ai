"""Row 621: Quota Management - Allocates resources.

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


def evaluate_allocations(rows):
    """Rows: (consumer, allocated_units, requested_units). Supplied
    allocations from a fixed100unit pool. Refuse overallocated pool; each
    indivisible request accepted if within its consumer allocation, otherwise
    consumes zero. Local supplied-data report, no real reservation/admission,
    distributed accounting, quota reset or customer enforcement.
    """
    _rows(rows, 3)
    for consumer,allocation,request in rows:
        _label(consumer)
        _integer(allocation, 0, 100)
        _integer(request, 0, 1000000)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate consumer')
    allocated=sum(x[1] for x in rows)
    if allocated>100:
        raise ValueError('pool overallocated')
    consumers=[]
    for consumer,allocation,request in sorted(rows):
        accepted=request<=allocation
        used=request if accepted else 0
        consumers.append((consumer,accepted,used,allocation-used))
    return {'consumers':consumers,'allocated':allocated,'unallocated':100-allocated,
            'used':sum(x[2] for x in consumers)}
