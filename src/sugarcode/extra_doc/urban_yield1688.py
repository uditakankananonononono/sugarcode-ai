"""Urban Agriculture.

PARTIAL: caller harvest/area ratio ledger only, not urban agriculture,
crop yield prediction, land suitability, food safety or growing recommendations.
Caller compatible quantities are declarations, not verified farming data.
"""
from fractions import Fraction
SCOPE='caller harvest-area ratio ledger only; no urban agriculture claims'


def area(rows):
    """Exactlist/tuple1..64 triples(label,harvest,area);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint harvest0..1000000,
    area1..1000000. Sorted(label,total harvest,total area,ratio),overall
    harvest/area ratio. Mixedrows accepted;no species,size,time,gear,sampling
    standardization or sustainable yield inferred from ratios.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,harvest,area=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(harvest) is not int or type(area) is not int or not 0<=harvest<=1000000 or not 1<=area<=1000000:raise ValueError('harvest must be exactint0..1000000 and area exactint1..1000000')
        old_harvest,old_area=groups.get(label,(0,0));groups[label]=(old_harvest+harvest,old_area+area)
    result=tuple((label,harvest,area,Fraction(harvest,area)) for label,(harvest,area) in sorted(groups.items()))
    total_harvest=sum(row[1] for row in result);total_area=sum(row[2] for row in result)
    return {'area':result,'total_harvest':total_harvest,'total_area':total_area,'overall_ratio':Fraction(total_harvest,total_area),'scope':SCOPE}
