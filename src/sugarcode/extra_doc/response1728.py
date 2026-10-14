"""Doc row1728 Response Rate Improvement: PARTIAL supplied round-rate comparison.

Rows exact list1..50 unique tuples(id,invited,responded); nonblank exact str<=80,
invited exact int1..10000, responded exact int0..invited. Output exact response
rate pairs, rank descending then ID, aggregate rate. No intervention, causal
improvement, recruitment or actual survey response verification claimed.
"""
from fractions import Fraction


def compare(rows):
    if type(rows) is not list or not 1<=len(rows)<=50:
        raise ValueError('rows must be an exact list with 1..50 entries')
    ids=set()
    for row in rows:
        if type(row) is not tuple or len(row)!=3:
            raise ValueError('row must be an id invited responded tuple')
        name,invited,responded=row
        if type(name) is not str or not 1<=len(name)<=80 or not name.strip() or name in ids:
            raise ValueError('IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(name)
        if type(invited) is not int or not 1<=invited<=10000:
            raise ValueError('invited must be an integer in 1..10000')
        if type(responded) is not int or not 0<=responded<=invited:
            raise ValueError('responded must be an integer in 0..invited')
    values=sorted([(n,Fraction(r,i)) for n,i,r in rows],key=lambda x:(-x[1],x[0]))
    total=Fraction(sum(r for n,i,r in rows),sum(i for n,i,r in rows))
    return {'ranking':[(n,(v.numerator,v.denominator)) for n,v in values],
            'aggregate_rate':(total.numerator,total.denominator),'claim':'PARTIAL','improvement_validated':False}
