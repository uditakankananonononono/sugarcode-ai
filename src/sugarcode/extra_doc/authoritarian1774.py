"""Doc row1774 Authoritarianism: PARTIAL supplied decision-share concentration.

Bodies exact list2..20 tuples(id,decisions), unique exact nonblank str1..80 IDs;
decisions exact int0..1000, positive sum required. Return exact shares and sum
of squared shares. No actual authoritarianism, regime status or political inference.
"""
from fractions import Fraction


def concentration(bodies):
    if type(bodies) is not list or not 2<=len(bodies)<=20:raise ValueError('bodies must be an exact list with 2..20 entries')
    ids=set()
    for row in bodies:
        if type(row) is not tuple or len(row)!=2:raise ValueError('body must be an id decisions tuple')
        n,d=row
        if type(n) is not str or not 1<=len(n)<=80 or not n.strip() or n in ids:raise ValueError('body IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(n)
        if type(d) is not int or not 0<=d<=1000:raise ValueError('decisions must be an integer in 0..1000')
    total=sum(d for n,d in bodies)
    if total==0:raise ValueError('total decisions must be positive')
    shares=[(n,Fraction(d,total)) for n,d in bodies];h=sum((s*s for n,s in shares),Fraction(0))
    return {'shares':[(n,(s.numerator,s.denominator)) for n,s in shares],'concentration':(h.numerator,h.denominator),'claim':'PARTIAL','regime_inferred':False}
