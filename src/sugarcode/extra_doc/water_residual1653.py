"""Water Treatment.

PARTIAL: caller concentration/removal-fraction arithmetic only, not water
purification, contaminant testing, potability or treatment recommendations.
No drinking-water limits, health conclusions or process efficiency are inferred.
"""
from fractions import Fraction
SCOPE='caller concentration-removal arithmetic only; no water safety claims'


def residuals(rows):
    """Exactlist/tuple1..64 quads(label,initial,removed numerator,denominator).
    Unique printable Unicode exactstr labels1..40;exactint initial0..1000000,
    0<=numerator<=denominator<=1000000,denominator>0. Sorted(label,residual,
    removed quantity),sum residuals. Units are caller compatible abstractions;
    summing concentrations has no inferred physical meaning. Mixedrows accepted.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,initial,numerator,denominator=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(initial) is not int or type(numerator) is not int or type(denominator) is not int or not 0<=initial<=1000000 or not 0<=numerator<=denominator<=1000000 or denominator==0:raise ValueError('initial must be exactint0..1000000 and removal exactint0<=numerator<=denominator<=1000000 with denominator>0')
        removed=Fraction(initial*numerator,denominator);parsed.append((label,initial-removed,removed))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'residuals':result,'total_residual':sum(row[1] for row in result),'scope':SCOPE}
