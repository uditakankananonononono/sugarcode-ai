"""Air Pollution Control.

PARTIAL: caller staged removal-fraction arithmetic only, not pollution control,
equipment performance, emissions compliance or health/environmental advice.
Caller removal factors are not measured or certified control efficiencies.
"""
from fractions import Fraction
SCOPE='caller staged removal-fraction arithmetic only; no air pollution control claims'


def stages(rows,initial):
    """Exactlist/tuple0..64 triples(label,removal numerator,denominator);unique
    printable Unicode exactstr labels1..40;exactint0<=numerator<=denominator
    <=1000000,denominator>0;initial exactint0..1000000. Preserve order;
    (label,residual,removed),final,total removed. Empty final=initial.
    Mixedrows accepted;no chemistry,physical units or control design inferred.
    """
    if type(initial) is not int or not 0<=initial<=1000000:raise ValueError('initial must be exactint0..1000000')
    if type(rows) not in (list,tuple) or len(rows)>64:raise ValueError('rows must be exactlist/tuple atmost64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,numerator,denominator=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(numerator) is not int or type(denominator) is not int or not 0<=numerator<=denominator<=1000000 or denominator==0:raise ValueError('removal must be exactint0<=numerator<=denominator<=1000000 with denominator>0')
        parsed.append((label,Fraction(numerator,denominator)))
    residual=Fraction(initial);result=[]
    for label,fraction in parsed:
        removed=residual*fraction;residual-=removed;result.append((label,residual,removed))
    return {'stages':tuple(result),'final':residual,'total_removed':initial-residual,'scope':SCOPE}
