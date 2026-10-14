"""Doc row1771 Social Movements: PARTIAL supplied event participation ledger.

Events exact list1..20 (id,participants), unique valid IDs; participants exact
list0..100 unique labels. Labels exact nonblank str1..80. Return distinct supplied
participants, attendance count per participant, consecutive event overlap counts.
No real movement, membership, cause, ideology or social inference.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_attendance(events):
    if type(events) is not list or not 1<=len(events)<=20:raise ValueError('events must be an exact list with 1..20 entries')
    ids=set()
    for row in events:
        if type(row) is not tuple or len(row)!=2:raise ValueError('event must be an id participants tuple')
        n,participants=row
        if not _label(n) or n in ids:raise ValueError('event IDs must be unique valid labels')
        ids.add(n)
        if type(participants) is not list or len(participants)>100 or any(not _label(x) for x in participants) or len(set(participants))!=len(participants):raise ValueError('participants must be an exact list of 0..100 unique valid labels')
    people=sorted({p for n,pp in events for p in pp})
    return {'participants':people,'attendance':[(p,sum(p in pp for n,pp in events)) for p in people],'overlap':[(a,b,len(set(ap)&set(bp))) for (a,ap),(b,bp) in zip(events,events[1:])],'claim':'PARTIAL','movement_validated':False}
