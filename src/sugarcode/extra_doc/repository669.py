"""Row 669: Repository Pattern - Abstracts data access.

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


def run_repository_operations(rows):
    """Rows: (operation_id, key, op0=put/1=get/2=delete, scalar_value).
    In-memory repository interface: put replaces, get missing returns None,
    delete returns whether present. Get/delete value slot validated but ignored.
    Ordered operations; return trace and final sorted snapshot. No durable DB,
    network, transaction/concurrency semantics or arbitrary backend adapter.
    """
    _rows(rows, 4)
    for operation,key,op,value in rows:
        _label(operation)
        _label(key)
        _integer(op, 0, 2)
        _integer(value, -1000000, 1000000)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate operation')
    class Repository:
        def __init__(self):
            self.data={}
        def put(self,key,value):
            self.data[key]=value
            return value
        def get(self,key):
            return self.data.get(key)
        def delete(self,key):
            present=key in self.data
            if present:
                del self.data[key]
            return present
    repository=Repository()
    trace=[]
    for operation,key,op,value in rows:
        if op==0:
            result=repository.put(key,value)
        elif op==1:
            result=repository.get(key)
        else:
            result=repository.delete(key)
        trace.append((operation,result))
    return {'operations':trace,'records':sorted(repository.data.items())}
