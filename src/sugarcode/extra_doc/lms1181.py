"""Row1181 Adolescent Medicine: PARTIAL supplied LMS Box-Cox standard scores.
Exact list1..12 tuples(label,x,M,L,Snum,Sden). Unique printable ASCII labels
1..24; x,M exact int1..100; L exact int1..3 (zero/log branch excluded);
Snum,Sden exact int1..10. z=((x/M)^L-1)/(L*S), S=Snum/Sden.
Returns exact scores; supplied reference parameters are not validated or chosen.
No percentile conversion, growth diagnosis or medical recommendation.
NOT_CLAIMED: reference validity, diagnosis, clinical advice, production readiness.
"""
from fractions import Fraction as F
SCOPE='PARTIAL: exact supplied positive-integer-L LMS standard scores'
NOT_CLAIMED=('reference validity','diagnosis','clinical advice','production readiness')

def scores(rows):
    if type(rows) is not list or not 1<=len(rows)<=12:raise ValueError('rows must be exact list1..12')
    seen=set()
    for row in rows:
        if type(row) is not tuple or len(row)!=6:raise ValueError('row must be exact tuple6')
        label,x,m,l,a,b=row
        if type(label) is not str or not 1<=len(label)<=24 or not (label.isascii() and label.isprintable()) or label in seen:raise ValueError('labels must be unique printable ASCII strings1..24')
        seen.add(label)
        for v,hi in [(x,100),(m,100),(l,3),(a,10),(b,10)]:
            if type(v) is not int or not 1<=v<=hi:raise ValueError('bounded exact positive integer required')
    return {'scores':[(label,(F(x,m)**l-1)/(l*F(a,b))) for label,x,m,l,a,b in rows],'reference_validated':False}
