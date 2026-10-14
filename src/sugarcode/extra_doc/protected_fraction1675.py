"""Protected Areas.

PARTIAL: caller total/protected area arithmetic only, not protected-area
mapping, legal designation, conservation effectiveness or management advice.
Caller areas are declarations, not verified boundaries or legal protections.
"""
from fractions import Fraction
SCOPE='caller total-protected area arithmetic only; no protected-area status claims'


def coverage(rows):
    """Exactlist/tuple1..64 triples(label,total,protected);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint0<=protected<=total
    <=1000000. Sorted(label,total sum,protected sum,unprotected,fraction or
    None at zero total),aggregate unprotected and protected fraction.
    Mixedrows accepted;no overlap removal,habitat quality or designation inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,total,protected=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(total) is not int or type(protected) is not int or not 0<=protected<=total<=1000000:raise ValueError('areas must be exactint0<=protected<=total<=1000000')
        old_total,old_protected=groups.get(label,(0,0));groups[label]=(old_total+total,old_protected+protected)
    result=tuple((label,total,protected,total-protected,Fraction(protected,total) if total else None) for label,(total,protected) in sorted(groups.items()))
    total=sum(row[1] for row in result);protected=sum(row[2] for row in result)
    return {'coverage':result,'unprotected':total-protected,'protected_fraction':Fraction(protected,total) if total else None,'scope':SCOPE}
