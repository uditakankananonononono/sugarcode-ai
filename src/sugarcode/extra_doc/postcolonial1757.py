"""Doc row1757 Postcolonial Theory: PARTIAL supplied resource-transfer ledger.

Actors exact list2..20 unique nonblank exact str1..80. Transfers exact list0..100
(source,target,units) tuples, endpoints known labels and distinct, units exact
int1..1000. Duplicate transfers allowed as separate supplied events. Return
received, sent, net per actor in input order. No colonial identity, exploitation,
causal, historical or postcolonial theory inference.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_transfers(actors,transfers):
    if type(actors) is not list or not 2<=len(actors)<=20 or any(not _label(x) for x in actors) or len(set(actors))!=len(actors):raise ValueError('actors must be an exact list of 2..20 unique valid labels')
    if type(transfers) is not list or len(transfers)>100:raise ValueError('transfers must be an exact list with 0..100 entries')
    for row in transfers:
        if type(row) is not tuple or len(row)!=3:raise ValueError('transfer must be a source target units tuple')
        a,b,units=row
        if not _label(a) or not _label(b) or a not in actors or b not in actors or a==b:raise ValueError('endpoints must be distinct known valid labels')
        if type(units) is not int or not 1<=units<=1000:raise ValueError('units must be an integer in 1..1000')
    balances=[]
    for n in actors:
        incoming=sum(u for a,b,u in transfers if b==n);outgoing=sum(u for a,b,u in transfers if a==n)
        balances.append((n,incoming,outgoing,incoming-outgoing))
    return {'balances':balances,'total_transferred':sum(u for a,b,u in transfers),'claim':'PARTIAL','history_validated':False}
