"""Row 622: Multi-Tenancy - Serves multiple customers.

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


def read_tenant_records(rows):
    """Rows: (requesting_tenant, owner_tenant, record_id, value).
    Supplied-identity isolation decision: equal tenant labels expose supplied
    value; others return None. Identity labels are NOT authenticated. Local
    simulator, no real datastore isolation/authorization/customer service.
    """
    _rows(rows, 4)
    for requester,owner,record,value in rows:
        _label(requester)
        _label(owner)
        _label(record)
        _integer(value, -1000000, 1000000)
    identities=[x[:3] for x in rows]
    if len(set(identities))!=len(rows):
        raise ValueError('duplicate access request')
    stored={}
    for _,owner,record,value in rows:
        key=(owner,record)
        if key in stored and stored[key]!=value:
            raise ValueError('conflicting record value')
        stored[key]=value
    accesses=[]
    for requester,owner,record,value in sorted(rows):
        allowed=requester==owner
        accesses.append((requester,owner,record,allowed,value if allowed else None))
    return {'accesses':accesses,'denied_count':sum(not x[3] for x in accesses)}
