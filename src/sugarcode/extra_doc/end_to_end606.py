"""Row606 End-to-End Testing - Tests full flows.

Bounded fixed checkout state-machine simulation: cart -> paid -> shipped. No
actual commerce, payment, shipping, UI, browser, user data or external calls.
The complete simulated flow is executed, not a deployed full-flow test claim.
"""


def exercise_flow(events):
    """Exact list1..32 tuple(event_id, action); actions add/pay/ship.
    add requires cart, pay requires a nonempty cart, ship requires paid state.
    Invalid transition stops with a fault and retains previous state.
    All schemas/IDs/actions validated before processing. IDs unique.
    """
    if type(events) is not list:
        raise TypeError('exact event list required')
    if not 1<=len(events)<=32:
        raise ValueError('event count must be 1..32')
    import re
    for row in events:
        if type(row) is not tuple:
            raise TypeError('exact tuple event required')
        if len(row)!=2:
            raise ValueError('event arity must be two')
        event,action=row
        if type(event) is not str:
            raise TypeError('exact event identifier string required')
        if not 1<=len(event)<=24 or re.fullmatch(r'[a-z][a-z0-9_]*',event) is None:
            raise ValueError('bounded lowercase event identifier required')
        if type(action) is not str:
            raise TypeError('exact action string required')
        if action not in ('add','pay','ship'):
            raise ValueError('unknown flow action')
    if len({x[0] for x in events})!=len(events):
        raise ValueError('duplicate event')
    state='cart'
    items=0
    trace=[]
    fault=None
    for event,action in events:
        before=state
        if action=='add' and state=='cart':
            items+=1
        elif action=='pay' and state=='cart' and items>0:
            state='paid'
        elif action=='ship' and state=='paid':
            state='shipped'
        else:
            fault=(event,'invalid_transition')
            break
        trace.append((event,action,before,state,items))
    return {'state':state,'items':items,'trace':trace,'fault':fault,
            'complete_simulated_flow':state=='shipped' and fault is None}
