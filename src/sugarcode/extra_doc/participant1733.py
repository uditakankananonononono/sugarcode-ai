"""Doc row1733 Participant Observation: PARTIAL supplied observation coverage.

Slots exact list1..50 tuples(setting,activity), unique pairs; observations exact
list0..100 tuples(id,setting,activity,duration), distinct IDs; labels nonblank
exact str<=80, duration exact int1..60. Report uncovered slots, unknown observation
IDs, and per-slot observation count/minutes input slot order. No real presence,
research ethics, observational validity or participant inference claimed.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit(slots,observations):
    if type(slots) is not list or not 1<=len(slots)<=50:
        raise ValueError('slots must be an exact list with 1..50 entries')
    if any(type(r) is not tuple or len(r)!=2 or any(not _label(x) for x in r) for r in slots) or len(set(slots))!=len(slots):
        raise ValueError('slots must be unique valid setting activity tuples')
    if type(observations) is not list or len(observations)>100:
        raise ValueError('observations must be an exact list with 0..100 entries')
    ids=set()
    for row in observations:
        if type(row) is not tuple or len(row)!=4:
            raise ValueError('observation must be an id setting activity duration tuple')
        name,setting,activity,duration=row
        if any(not _label(x) for x in (name,setting,activity)) or name in ids:
            raise ValueError('observation labels must be valid with unique IDs')
        ids.add(name)
        if type(duration) is not int or not 1<=duration<=60:raise ValueError('duration must be an integer in 1..60')
    coverage={slot:[0,0] for slot in slots};unknown=[]
    for name,setting,activity,duration in observations:
        if (setting,activity) in coverage:coverage[setting,activity][0]+=1;coverage[setting,activity][1]+=duration
        else:unknown.append(name)
    return {'coverage':[(s,a,*coverage[s,a]) for s,a in slots],'uncovered':[slot for slot in slots if coverage[slot][0]==0],
            'unknown':unknown,'claim':'PARTIAL','observation_validated':False}
