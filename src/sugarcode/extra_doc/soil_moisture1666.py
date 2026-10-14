"""Soil Health.

PARTIAL: caller wet/dry mass moisture arithmetic only, not soil health,
soil testing, crop suitability, fertility or agronomic recommendations.
Caller masses are abstract compatible units, not verified soil measurements.
"""
from fractions import Fraction
SCOPE='caller wet-dry mass moisture arithmetic only; no soil health or agronomic claims'


def moisture(rows):
    """Exactlist/tuple1..64 triples(label,wet,dry);printable Unicode exactstr
    labels1..40,repeated labels aggregate;exactint0<=dry<=wet<=1000000.
    Sorted(label,wet total,dry total,water,water/dry or None at zero dry),total
    water and aggregate dry-basis moisture fraction. Mixedrows accepted.
    No water availability,texture,organic content,pH or biological conclusions.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,wet,dry=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(wet) is not int or type(dry) is not int or not 0<=dry<=wet<=1000000:raise ValueError('masses must be exactint0<=dry<=wet<=1000000')
        old_wet,old_dry=groups.get(label,(0,0));groups[label]=(old_wet+wet,old_dry+dry)
    result=tuple((label,wet,dry,wet-dry,Fraction(wet-dry,dry) if dry else None) for label,(wet,dry) in sorted(groups.items()))
    total_water=sum(row[3] for row in result);total_dry=sum(row[2] for row in result)
    return {'moisture':result,'total_water':total_water,'dry_basis_fraction':Fraction(total_water,total_dry) if total_dry else None,'scope':SCOPE}
