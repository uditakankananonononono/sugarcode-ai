"""Waste-to-Energy.

PARTIAL: caller mass/energy-factor multiplication only, not waste-to-energy,
combustion, gasification, emissions accounting or plant performance modeling.
Factors and compatible units are caller declarations, not verified energy data.
"""
from fractions import Fraction
SCOPE='caller mass-energy-factor arithmetic only; no waste-to-energy performance claims'


def energy(rows):
    """Exactlist/tuple1..64 quads(label,mass,numerator,denominator);unique
    printable Unicode exactstr labels1..40;exactint mass,numerator0..1000000,
    denominator1..1000000. Sorted(label,mass*numerator/denominator),total
    and strictly positive labels. Mixedrows accepted. No efficiency,calorific
    assumptions,emissions,units,technology or cost estimates are inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,mass,numerator,denominator=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(mass) is not int or type(numerator) is not int or type(denominator) is not int or not 0<=mass<=1000000 or not 0<=numerator<=1000000 or not 1<=denominator<=1000000:raise ValueError('mass and numerator must be exactint0..1000000 and denominator exactint1..1000000')
        parsed.append((label,Fraction(mass*numerator,denominator)))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'energy':result,'total':sum(value for label,value in result),'positive':tuple(label for label,value in result if value>0),'scope':SCOPE}
