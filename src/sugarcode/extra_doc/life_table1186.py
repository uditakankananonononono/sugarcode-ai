"""Row1186 Global Health: PARTIAL exact closed-cohort abridged life table.
Supplied exact list1..12 tuples(label,width,rate_num,rate_den,ax_num,ax_den).
Unique printable ASCII exact strings1..24; width exact int1..10, rate_num
exact int0..10,rate_den exact int1..10, ax_num exact int0..10,ax_den exact
int1..10; ax=ax_num/ax_den must be between0andwidth. Rates are supplied
mortality rates, not estimated. q=n*m/(1+(n-ax)*m), capped at1. Unit radix;
deaths=l*q, L=n*(l-deaths)+ax*deaths. Reverse-sum L for restricted remaining
person-years and restricted expectancy T/l, None when l=0. Terminal survivors
are censored, not assigned an open-ended lifespan. No clinical recommendations.
NOT_CLAIMED: representative mortality, full lifespan, clinical advice, production readiness.
"""
from fractions import Fraction as F
SCOPE='PARTIAL: closed-cohort supplied-rate restricted abridged life table'
NOT_CLAIMED=('representative mortality','full lifespan','clinical advice','production readiness')


def table(rows):
    if type(rows) is not list or not 1<=len(rows)<=12:raise ValueError('rows must be exact list1..12')
    seen=set()
    for row in rows:
        if type(row) is not tuple or len(row)!=6:raise ValueError('row must be exact tuple6')
        label,n,r,d,a,b=row
        if type(label) is not str or not 1<=len(label)<=24 or not (label.isascii() and label.isprintable()) or label in seen:raise ValueError('labels must be unique printable ASCII strings1..24')
        seen.add(label)
        for v,lo,hi in [(n,1,10),(r,0,10),(d,1,10),(a,0,10),(b,1,10)]:
            if type(v) is not int or not lo<=v<=hi:raise ValueError('bounded exact integer required')
        if F(a,b)>n:raise ValueError('ax must not exceed width')
    alive=F(1);trace=[]
    for label,n,r,d,a,b in rows:
        ax=F(a,b);rate=F(r,d);q=min(F(1),n*rate/(1+(n-ax)*rate));dead=alive*q;area=n*(alive-dead)+ax*dead
        trace.append((label,alive,q,dead,area));alive-=dead
    total=F(0);remaining=[]
    for label,l,q,d,L in reversed(trace):
        total+=L;remaining.append((total,total/l if l else None))
    remaining.reverse()
    return {'intervals':[(label,l,q,d,L,T,e) for (label,l,q,d,L),(T,e) in zip(trace,remaining)],'survivors':alive,'restricted_expectancy':total,'population_validated':False}
