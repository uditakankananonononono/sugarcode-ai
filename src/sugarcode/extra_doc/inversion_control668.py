"""Row 668: Inversion of Control - Delegates decisions.

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


def run_framework_events(rows):
    """Rows: (event_id, handler0=increment/1=reset, scalar_value). A fixed
    local framework consumes events in supplied order and selects its internal
    handler. Increment adds value; reset replaces state. Returns state trace.
    No caller arbitrary callbacks, service framework, asynchronous lifecycle or
    general IoC container. Restricted local event-loop demonstration.
    """
    _rows(rows, 3)
    for event,handler,value in rows:
        _label(event)
        _integer(handler, 0, 1)
        _integer(value, -1000000, 1000000)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate event')
    def increment(state,value):
        return state+value
    def reset(state,value):
        return value
    handlers=(increment,reset)
    state=0
    trace=[]
    for event,handler,value in rows:
        state=handlers[handler](state,value)
        trace.append((event,state))
    return {'events':trace,'state':state}
