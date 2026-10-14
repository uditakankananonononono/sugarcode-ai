"""Doc row1745 Narrative Analysis: PARTIAL supplied event chronology audit.

Events exact list1..100 tuples(id,time,actors); unique exact nonblank str IDs1..80,
time exact int0..100, actors exact list0..20 unique labels1..80. Return chronological
IDs, input-order inversions (strict time decrease pairs), tied groups, actor spans.
No inferred narrative, plot, causality, meaning or authenticity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_events(events):
    if type(events) is not list or not 1<=len(events)<=100:raise ValueError('events must be an exact list with 1..100 entries')
    ids=set()
    for row in events:
        if type(row) is not tuple or len(row)!=3:raise ValueError('event must be an id time actors tuple')
        name,time,actors=row
        if not _label(name) or name in ids:raise ValueError('event IDs must be unique valid labels')
        ids.add(name)
        if type(time) is not int or not 0<=time<=100:raise ValueError('time must be an integer in 0..100')
        if type(actors) is not list or len(actors)>20 or any(not _label(x) for x in actors) or len(set(actors))!=len(actors):raise ValueError('actors must be an exact list of 0..20 unique valid labels')
    ordered=sorted(events,key=lambda e:(e[1],e[0]))
    inversions=[(a[0],b[0]) for i,a in enumerate(events) for b in events[i+1:] if a[1]>b[1]]
    times=sorted({t for n,t,actors in events})
    ties=[(t,sorted(n for n,time,a in events if time==t)) for t in times if sum(time==t for n,time,a in events)>1]
    spans=[]
    for actor in sorted({a for n,t,actors in events for a in actors}):
        at=[t for n,t,actors in events if actor in actors];spans.append((actor,min(at),max(at)))
    return {'chronology':[n for n,t,a in ordered],'inversions':inversions,'ties':ties,'actor_spans':spans,'claim':'PARTIAL','narrative_validated':False}
