"""Doc row1767 Coalition Theory: PARTIAL supplied weighted coalition fixture.

Players exact list2..10 (id,weight) tuples, unique nonblank exact str IDs1..80,
weight exact int1..100. Quota exact int1..1000. Enumerate every nonempty winning
coalition and minimal winning coalitions in bitmask order, members in input order.
No real alliances, political influence or coalition behavior.
"""


def enumerate_coalitions(players,quota):
    if type(players) is not list or not 2<=len(players)<=10:raise ValueError('players must be an exact list with 2..10 entries')
    ids=set()
    for row in players:
        if type(row) is not tuple or len(row)!=2:raise ValueError('player must be an id weight tuple')
        n,w=row
        if type(n) is not str or not 1<=len(n)<=80 or not n.strip() or n in ids:raise ValueError('player IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(n)
        if type(w) is not int or not 1<=w<=100:raise ValueError('weight must be an integer in 1..100')
    if type(quota) is not int or not 1<=quota<=1000:raise ValueError('quota must be an integer in 1..1000')
    winning=[];minimal=[]
    for mask in range(1,1<<len(players)):
        chosen=[(n,w) for i,(n,w) in enumerate(players) if mask&(1<<i)];total=sum(w for n,w in chosen)
        if total>=quota:
            names=[n for n,w in chosen];winning.append((names,total))
            if all(total-w<quota for n,w in chosen):minimal.append((names[:],total))
    return {'winning':winning,'minimal':minimal,'claim':'PARTIAL','coalitions_validated':False}
