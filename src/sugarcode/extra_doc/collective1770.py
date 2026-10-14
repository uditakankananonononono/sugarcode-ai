"""Doc row1770 Collective Action: PARTIAL supplied contribution threshold ledger.

Participants exact list1..100 tuples(id,units), unique exact nonblank str1..80
IDs; units exact int0..1000. Threshold exact int1..10000. Return total, shortfall,
met flag, pivotal participants whose removal changes met to unmet. No actual
participation, motives, coordination, public-goods or collective-action validity.
"""


def audit_contributions(participants,threshold):
    if type(participants) is not list or not 1<=len(participants)<=100:raise ValueError('participants must be an exact list with 1..100 entries')
    ids=set()
    for row in participants:
        if type(row) is not tuple or len(row)!=2:raise ValueError('participant must be an id units tuple')
        n,u=row
        if type(n) is not str or not 1<=len(n)<=80 or not n.strip() or n in ids:raise ValueError('participant IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(n)
        if type(u) is not int or not 0<=u<=1000:raise ValueError('units must be an integer in 0..1000')
    if type(threshold) is not int or not 1<=threshold<=10000:raise ValueError('threshold must be an integer in 1..10000')
    total=sum(u for n,u in participants);met=total>=threshold
    return {'total':total,'shortfall':max(0,threshold-total),'met':met,'pivotal':[n for n,u in participants if met and total-u<threshold],'claim':'PARTIAL','action_validated':False}
