"""Watershed Management.

PARTIAL: caller area/weight ledger only, not watershed management, runoff
prediction, catchment modeling, erosion assessment or hydrological advice.
Caller weights and compatible areas are abstract, not calibrated coefficients.
"""
from fractions import Fraction
SCOPE='caller area-weight ledger only; no watershed or runoff prediction'


def weights(rows):
    """Exactlist/tuple1..64 quads(label,area,weight numerator,denominator);
    unique printable Unicode exactstr labels1..40;exactint area0..1000000,
    0<=numerator<=denominator<=1000000,denominator>0. Sorted(label,weighted
    area),total area,weighted total and weighted average (None at zero area).
    Mixedrows accepted;no rainfall,runoff,land use,soil or terrain assumptions.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[];total_area=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,area,numerator,denominator=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(area) is not int or type(numerator) is not int or type(denominator) is not int or not 0<=area<=1000000 or not 0<=numerator<=denominator<=1000000 or denominator==0:raise ValueError('area must be exactint0..1000000 and weight exactint0<=numerator<=denominator<=1000000 with denominator>0')
        total_area+=area;parsed.append((label,Fraction(area*numerator,denominator)))
    result=tuple(sorted(parsed,key=lambda row:row[0]));weighted=sum(value for label,value in result)
    return {'weighted_areas':result,'area':total_area,'weighted_total':weighted,'weighted_average':weighted/total_area if total_area else None,'scope':SCOPE}
