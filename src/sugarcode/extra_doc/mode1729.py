"""Doc row1729 Survey Mode Effects: PARTIAL paired-score comparison fixture.

Rows exact list1..50 tuples(id,mode_a,mode_b), unique labels nonblank exact str<=80,
exact nonbool scores0..100. Differences mode_b-mode_a, exact mean difference,
counts positive/negative/equal. No causal mode effects or survey bias diagnosis.
"""
from fractions import Fraction


def compare(rows):
    if type(rows) is not list or not 1<=len(rows)<=50:
        raise ValueError('rows must be an exact list with 1..50 entries')
    ids=set()
    for row in rows:
        if type(row) is not tuple or len(row)!=3:
            raise ValueError('row must be an id mode-a mode-b tuple')
        name,a,b=row
        if type(name) is not str or not 1<=len(name)<=80 or not name.strip() or name in ids:
            raise ValueError('IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(name)
        if any(type(x) is not int or not 0<=x<=100 for x in (a,b)):
            raise ValueError('scores must be exact integers in 0..100')
    differences=[(n,b-a) for n,a,b in rows];mean=Fraction(sum(d for n,d in differences),len(rows))
    return {'differences':differences,'mean_difference':(mean.numerator,mean.denominator),
            'positive':sum(d>0 for n,d in differences),'negative':sum(d<0 for n,d in differences),
            'equal':sum(d==0 for n,d in differences),'claim':'PARTIAL','causal_effect_validated':False}
