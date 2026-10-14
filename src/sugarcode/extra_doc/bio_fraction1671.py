"""Bioremediation.

PARTIAL: caller staged remaining-fraction arithmetic only, not bioremediation,
microbial kinetics, contaminant degradation, treatment effectiveness or safety.
Caller fractions are abstract, not measured biological degradation rates.
"""
from fractions import Fraction
SCOPE='caller staged remaining-fraction arithmetic only; no bioremediation claims'


def remaining(rows,initial):
    """Exactlist/tuple0..64 triples(label,numerator,denominator);unique
    printable Unicode exactstr labels1..40;exactint0<=numerator<=denominator
    <=1000000,denominator>0;initial exactint0..1000000. Preserve order;
    (label,residual,stage change),final,total change. Empty final=initial.
    Mixedrows accepted;no species,rates,time or chemical products inferred.
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
        if type(numerator) is not int or type(denominator) is not int or not 0<=numerator<=denominator<=1000000 or denominator==0:raise ValueError('fraction must be exactint0<=numerator<=denominator<=1000000 with denominator>0')
        parsed.append((label,Fraction(numerator,denominator)))
    residual=Fraction(initial);result=[]
    for label,fraction in parsed:
        after=residual*fraction;result.append((label,after,after-residual));residual=after
    return {'remaining':tuple(result),'final':residual,'total_change':residual-initial,'scope':SCOPE}
