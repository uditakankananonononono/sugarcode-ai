"""Carbon Footprinting.

PARTIAL: caller activity/emission-factor products only, not carbon footprinting,
verified emissions, greenhouse-gas accounting or environmental certification.
Caller factors are abstract, not verified inventory or emission-factor data.
"""
from fractions import Fraction
SCOPE='caller activity-emission-factor arithmetic only; no verified carbon footprint claims'


def footprint(rows):
    """Exactlist/tuple1..64 quads(label,activity,numerator,denominator);unique
    printable Unicode exactstr labels1..40;exactint activity,numerator0..1000000,
    denominator1..1000000. Sorted(label,activity*numerator/denominator),total
    and strictly positive labels. Mixedrows accepted. No efficiency,calorific
    assumptions,emissions,units,technology or cost estimates are inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,activity,numerator,denominator=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(activity) is not int or type(numerator) is not int or type(denominator) is not int or not 0<=activity<=1000000 or not 0<=numerator<=1000000 or not 1<=denominator<=1000000:raise ValueError('activity and numerator must be exactint0..1000000 and denominator exactint1..1000000')
        parsed.append((label,Fraction(activity*numerator,denominator)))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'footprint':result,'total':sum(value for label,value in result),'positive':tuple(label for label,value in result if value>0),'scope':SCOPE}
