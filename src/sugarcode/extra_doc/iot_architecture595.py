"""Row 595: IoT Architecture - Connects devices.

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


def plan_gateway_load(rows):
    """Rows: (device_id, gateway_id, message_rate, supplied_gateway_capacity).
    Aggregate declared rates per gateway, require consistent capacity and flag
    overload. No discovery, provisioning, connectivity or deployed IoT control.
    """
    _rows(rows, 4)
    for device, gateway, rate, capacity in rows:
        _label(device)
        _label(gateway)
        _integer(rate, 0, 1000000)
        _integer(capacity, 1, 1000000)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate device')
    result=[]
    for gateway in sorted({x[1] for x in rows}):
        members=[x for x in rows if x[1]==gateway]
        capacities={x[3] for x in members}
        if len(capacities)!=1:
            raise ValueError('gateway capacity declarations must agree')
        capacity=next(iter(capacities))
        total=sum(x[2] for x in members)
        result.append((gateway,len(members),total,capacity,total>capacity))
    return {'gateways':result,'devices':len(rows)}
