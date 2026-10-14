"""Doc row1027 Outlier Detection: PARTIAL exact Tukey-fence fixture.

Input exact list4..100 nonbool integer values-1000..1000. Quartiles use median
of lower/upper sorted halves, excluding central value for odd sample size.
Fences Q1-3/2 IQR and Q3+3/2 IQR; outliers strictly outside (not equal).
Return normalized rational quartile/fence pairs and original outlier indexes.
This fixed convention does not identify true anomalies or diagnose causes.
"""
from fractions import Fraction


def _middle(v):
    n=len(v)
    return (v[(n-1)//2]+v[n//2])/2


def detect(values):
    if type(values) is not list or not 4<=len(values)<=100:
        raise ValueError('values must be an exact list with 4..100 entries')
    if any(type(x) is not int or not -1000<=x<=1000 for x in values):
        raise ValueError('values must be integers in -1000..1000')
    ordered=sorted(Fraction(x) for x in values);half=len(ordered)//2
    q1,q3=_middle(ordered[:half]),_middle(ordered[-half:])
    span=q3-q1;low=q1-Fraction(3,2)*span;high=q3+Fraction(3,2)*span
    pair=lambda x:(x.numerator,x.denominator)
    return {'q1':pair(q1),'q3':pair(q3),'low':pair(low),'high':pair(high),
            'outliers':[i for i,x in enumerate(values) if x<low or x>high],
            'claim':'PARTIAL','anomalies_validated':False}
