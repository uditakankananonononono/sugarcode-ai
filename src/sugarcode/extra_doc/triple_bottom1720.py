"""Doc row1720 Triple Bottom Line: PARTIAL supplied three-dimension score fixture.

Rows exact list1..50 unique tuples(id,people,planet,profit), exact nonbool int0..100.
IDs nonblank exact str<=80. Weights exact tuple3 of exact int0..10, positive sum.
Return weighted rational average and rank descending, lexical ID ties. No
ethical/economic validity, true triple-bottom-line or policy judgment claimed.
"""
from fractions import Fraction


def rank(rows,weights):
    if type(rows) is not list or not 1<=len(rows)<=50:
        raise ValueError('rows must be an exact list with 1..50 entries')
    if type(weights) is not tuple or len(weights)!=3 or any(type(x) is not int or not 0<=x<=10 for x in weights) or sum(weights)==0:
        raise ValueError('weights must be an exact triple of integers in 0..10 with positive sum')
    ids=set()
    for row in rows:
        if type(row) is not tuple or len(row)!=4:
            raise ValueError('row must be an id people planet profit tuple')
        name,*metrics=row
        if type(name) is not str or not 1<=len(name)<=80 or not name.strip() or name in ids:
            raise ValueError('IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(name)
        if any(type(x) is not int or not 0<=x<=100 for x in metrics):
            raise ValueError('metrics must be exact integers in 0..100')
    scores=[(r[0],Fraction(sum(w*x for w,x in zip(weights,r[1:])),sum(weights))) for r in rows]
    return {'ranking':[(n,(s.numerator,s.denominator)) for n,s in sorted(scores,key=lambda r:(-r[1],r[0]))],
            'claim':'PARTIAL','value_judgments_validated':False}
