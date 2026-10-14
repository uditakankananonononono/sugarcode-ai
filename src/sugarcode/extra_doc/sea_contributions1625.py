"""Sea Level Rise.

PARTIAL: caller additive scenario contribution arithmetic only, not sea-level
rise modeling,coastal inundation,climate projections or risk assessment.
Caller values have no inferred units,physical components or scientific validity.
"""
from fractions import Fraction
SCOPE='caller additive contribution arithmetic only; no sea-level or coastal projections'


def contributions(rows,baseline):
    """Rows exactlist/tuple0..64(label,num,den),unique printable Unicode exactstr
    label1..40;numerator exactint-1000000..1000000,denominator exactint1..1000000.
    Baseline exactint-1000000..1000000. Return label-sorted exact contributions,
    sum positive,sum negative,signed total,baseline+total. Mixedrows accepted.
    No temporal extrapolation,uncertainty,sea-level units or coastal geometry.
    """
    if type(baseline) is not int or not -1000000<=baseline<=1000000:raise ValueError('baseline must be exactint-1000000..1000000')
    if type(rows) not in (list,tuple) or len(rows)>64:raise ValueError('rows must be exactlist/tuple atmost64')
    labels=set();result=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,num,den=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(num) is not int or not -1000000<=num<=1000000:raise ValueError('numerator must be exactint-1000000..1000000')
        if type(den) is not int or not 1<=den<=1000000:raise ValueError('denominator must be exactint1..1000000')
        result.append((label,Fraction(num,den)))
    total=sum((value for _,value in result),Fraction(0))
    return {'contributions':tuple(sorted(result,key=lambda row:row[0])),
            'positive':sum((value for _,value in result if value>0),Fraction(0)),
            'negative':sum((value for _,value in result if value<0),Fraction(0)),
            'total':total,'scenario':baseline+total,'scope':SCOPE}
