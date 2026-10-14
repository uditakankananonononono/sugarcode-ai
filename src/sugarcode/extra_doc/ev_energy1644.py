"""Electric Vehicles.

PARTIAL: caller battery-energy trip ledger only, not electric vehicles,
range prediction,charging control,battery physics or route feasibility.
Charges/uses/capacity caller inputs,no efficiencies or vehicle telemetry inferred.
"""
SCOPE='caller battery-energy trip ledger only; no EV range or charging-control claims'


def ledger(rows,capacity,initial):
    """Exactlist/tuple1..64 rows(charge,use),exactint0..1000000;capacity exact
    int1..1000000,initial exactint0..capacity. Charge before use;charge capped
    at capacity,excess reported discarded. Use exceeding current charge refuses
    whole call (no partial output/effects). Return(index,endcharge,discarded),
    final charge,total use/discarded. Mixedrows accepted;units caller-compatible.
    No vehicle behavior,charging rates,degradation,weather or safety inferred.
    """
    if type(capacity) is not int or not 1<=capacity<=1000000:raise ValueError('capacity must be exactint1..1000000')
    if type(initial) is not int or not 0<=initial<=capacity:raise ValueError('initial must be exactint0..capacity')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=2:raise ValueError('row must be exactlist/tuple pair')
        charge,use=row
        if type(charge) is not int or type(use) is not int or not 0<=charge<=1000000 or not 0<=use<=1000000:raise ValueError('charge and use must be exactint0..1000000')
        parsed.append((charge,use))
    current=initial;result=[];uses=0;discarded_total=0
    for i,(charge,use) in enumerate(parsed):
        incoming=current+charge;discarded=max(incoming-capacity,0);current=min(incoming,capacity)
        if use>current:raise ValueError('use must not exceed current charge')
        current-=use;uses+=use;discarded_total+=discarded;result.append((i,current,discarded))
    return {'steps':tuple(result),'final_charge':current,'use_total':uses,'discarded_total':discarded_total,'scope':SCOPE}
