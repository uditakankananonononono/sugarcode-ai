"""Doc row1766 Bargaining Theory: PARTIAL supplied integer Nash product fixture.

Disagreement exact tuple2 exact ints0..1000. Offers exact list1..100 tuples
(id,a,b), unique nonblank exact str IDs1..80, a/b exact ints0..1000. Reject offers
below disagreement from candidate set, maximize product of integer gains, ties
in supplied order. No actual negotiation, fairness or bargaining behavior.
"""


def select_offers(disagreement,offers):
    if type(disagreement) is not tuple or len(disagreement)!=2 or any(type(x) is not int or not 0<=x<=1000 for x in disagreement):raise ValueError('disagreement must be a two-integer tuple in 0..1000')
    if type(offers) is not list or not 1<=len(offers)<=100:raise ValueError('offers must be an exact list with 1..100 entries')
    ids=set()
    for row in offers:
        if type(row) is not tuple or len(row)!=3:raise ValueError('offer must be an id a b tuple')
        n,a,b=row
        if type(n) is not str or not 1<=len(n)<=80 or not n.strip() or n in ids:raise ValueError('offer IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(n)
        if any(type(x) is not int or not 0<=x<=1000 for x in (a,b)):raise ValueError('offer payoffs must be exact integers in 0..1000')
    da,db=disagreement
    feasible=[(n,(a-da)*(b-db)) for n,a,b in offers if a>=da and b>=db]
    best=max((p for n,p in feasible),default=None)
    return {'products':feasible,'maximizers':[n for n,p in feasible if p==best],'infeasible':[n for n,a,b in offers if a<da or b<db],'claim':'PARTIAL','bargaining_validated':False}
