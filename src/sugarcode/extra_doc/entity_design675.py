"""Doc row675 Entity Design: PARTIAL offline identity/version reducer.

Exact list0..100 events (id,expected_version,value), exact tuple3. ID nonblank
exact str<=80; version exact nonbool int0..100; value exact str<=120 including
empty. A new ID expects0, each accepted write increments version; mismatched
versions reject without change. Report final values/versions and accepted and
rejected indexes. No database concurrency, durable identity or actual writes.
"""


def apply(events):
    if type(events) is not list or len(events)>100:
        raise ValueError('events must be an exact list with 0..100 entries')
    for row in events:
        if type(row) is not tuple or len(row)!=3:
            raise ValueError('event must be an id, expected version, value tuple')
        name,version,value=row
        if type(name) is not str or not 1<=len(name)<=80 or not name.strip():
            raise ValueError('ID must be a nonblank exact string of 1..80 characters')
        if type(version) is not int or not 0<=version<=100:
            raise ValueError('version must be an integer in 0..100')
        if type(value) is not str or len(value)>120:
            raise ValueError('value must be an exact string with 0..120 characters')
    state={};ok=[];bad=[]
    for i,(name,version,value) in enumerate(events):
        current=state.get(name,(0,''))[0]
        if version!=current:bad.append(i);continue
        state[name]=(current+1,value);ok.append(i)
    return {'entities':[(name,*state[name]) for name in sorted(state)],'accepted':ok,'rejected':bad,
            'claim':'PARTIAL','persisted':False}
