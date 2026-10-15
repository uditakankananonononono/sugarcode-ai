"""Row1184 Men's Health: PARTIAL supplied-cohort competing-event product integral.
Exact list1..12 tuples(label,risk,eventA,eventB,censored),unique printable ASCII
labels1..24. Counts exact int0..100 with risk1..100 and events sum<=risk.
Risk sets equal prior risk minus prior events and subsequent censoring.
Unit survival decreases by both causes; cause-specific cumulative incidences
increase by previous survival times event/risk. Discrete supplied event table,
not sex-specific disease prediction or treatment. No time values inferred.
NOT_CLAIMED: clinical validity, sex-specific estimates, clinical advice, production readiness.
"""
from fractions import Fraction as F
SCOPE='PARTIAL: exact supplied censored-cohort two-cause cumulative incidence'
NOT_CLAIMED=('clinical validity','sex-specific estimates','clinical advice','production readiness')

def incidence(rows):
    if type(rows) is not list or not 1<=len(rows)<=12:raise ValueError('rows must be exact list1..12')
    seen=set();prior=None
    for row in rows:
        if type(row) is not tuple or len(row)!=5:raise ValueError('row must be exact tuple5')
        label,r,a,b,c=row
        if type(label) is not str or not 1<=len(label)<=24 or not (label.isascii() and label.isprintable()) or label in seen:raise ValueError('labels must be unique printable ASCII strings1..24')
        seen.add(label)
        if any(type(v) is not int or not 0<=v<=100 for v in (r,a,b,c)) or r==0:raise ValueError('bounded exact counts required')
        if a+b+c>r:raise ValueError('events exceed risk')
        if prior is not None and r!=prior:raise ValueError('risk set mismatch')
        prior=r-a-b-c
    s=F(1);fa=fb=F(0);trace=[]
    for label,r,a,b,c in rows:
        fa+=s*F(a,r);fb+=s*F(b,r);s*=F(r-a-b,r);trace.append((label,s,fa,fb))
    return {'trace':trace,'survival':s,'cause_a':fa,'cause_b':fb,'clinical_validated':False}
