"""Doc row677 Domain Event: PARTIAL offline sequence replay fixture.

Events exact list0..100 tuples(id,entity,sequence,delta). Labels nonblank exact
str<=80. sequence nonbool int1..100; delta nonbool int-100..100. Duplicate event
IDs reject. Each entity expects sequence1 then consecutive increments. Rejected
IDs are not consumed; retry with same ID and valid sequence is allowed. Accepted
deltas accumulate integer balances. No durable log or actual domain mutations.
"""


def replay(events):
    if type(events) is not list or len(events)>100:
        raise ValueError('events must be an exact list with 0..100 entries')
    for row in events:
        if type(row) is not tuple or len(row)!=4:
            raise ValueError('event must be an id, entity, sequence, delta tuple')
        name,entity,sequence,delta=row
        if any(type(x) is not str or not 1<=len(x)<=80 or not x.strip() for x in (name,entity)):
            raise ValueError('IDs must be nonblank exact strings of 1..80 characters')
        if type(sequence) is not int or not 1<=sequence<=100:
            raise ValueError('sequence must be an integer in 1..100')
        if type(delta) is not int or not -100<=delta<=100:
            raise ValueError('delta must be an integer in -100..100')
    seen=set();state={};ok=[];bad=[]
    for i,(name,entity,sequence,delta) in enumerate(events):
        version,balance=state.get(entity,(0,0))
        if name in seen or sequence!=version+1:bad.append(i);continue
        seen.add(name);state[entity]=(sequence,balance+delta);ok.append(i)
    return {'entities':[(e,*state[e]) for e in sorted(state)],'accepted':ok,'rejected':bad,
            'claim':'PARTIAL','persisted':False}
