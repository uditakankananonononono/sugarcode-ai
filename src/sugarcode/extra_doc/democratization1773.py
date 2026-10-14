"""Doc row1773 Democratization: PARTIAL supplied criterion-score change ledger.

Criteria exact list1..20 unique exact nonblank str1..80. Waves exact list2..20
(time,scores) tuples, unique exact int time0..1000; scores exact list matching
criteria, exact int0..10. Sort time and return per-criterion first/last/delta and
exact mean per wave. No actual democracy status, political transition or causality.
"""
from fractions import Fraction


def compare_scores(criteria,waves):
    if type(criteria) is not list or not 1<=len(criteria)<=20 or any(type(c) is not str or not 1<=len(c)<=80 or not c.strip() for c in criteria) or len(set(criteria))!=len(criteria):raise ValueError('criteria must be an exact list of 1..20 unique valid labels')
    if type(waves) is not list or not 2<=len(waves)<=20:raise ValueError('waves must be an exact list with 2..20 entries')
    seen=set()
    for row in waves:
        if type(row) is not tuple or len(row)!=2:raise ValueError('wave must be a time scores tuple')
        t,scores=row
        if type(t) is not int or not 0<=t<=1000 or t in seen:raise ValueError('times must be unique exact integers in 0..1000')
        seen.add(t)
        if type(scores) is not list or len(scores)!=len(criteria) or any(type(x) is not int or not 0<=x<=10 for x in scores):raise ValueError('scores must be an exact list matching criteria with integers in 0..10')
    ordered=sorted(waves);first,last=ordered[0][1],ordered[-1][1]
    changes=[(c,first[i],last[i],last[i]-first[i]) for i,c in enumerate(criteria)]
    means=[]
    for t,scores in ordered:
        f=Fraction(sum(scores),len(criteria));means.append((t,(f.numerator,f.denominator)))
    return {'changes':changes,'means':means,'claim':'PARTIAL','democracy_inferred':False}
