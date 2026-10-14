"""Fisheries Management.

PARTIAL: caller catch/effort ratio ledger only, not fisheries management,
stock assessment, sustainable catch limits or ecological recommendations.
Caller compatible quantities are not verified catches or fishing effort data.
"""
from fractions import Fraction
SCOPE='caller catch-effort ratio ledger only; no fisheries management advice'


def effort(rows):
    """Exactlist/tuple1..64 triples(label,catch,effort);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint catch0..1000000,
    effort1..1000000. Sorted(label,total catch,total effort,ratio),overall
    catch/effort ratio. Mixedrows accepted;no species,size,time,gear,sampling
    standardization or sustainable yield inferred from ratios.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,catch,effort=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(catch) is not int or type(effort) is not int or not 0<=catch<=1000000 or not 1<=effort<=1000000:raise ValueError('catch must be exactint0..1000000 and effort exactint1..1000000')
        old_catch,old_effort=groups.get(label,(0,0));groups[label]=(old_catch+catch,old_effort+effort)
    result=tuple((label,catch,effort,Fraction(catch,effort)) for label,(catch,effort) in sorted(groups.items()))
    total_catch=sum(row[1] for row in result);total_effort=sum(row[2] for row in result)
    return {'effort':result,'total_catch':total_catch,'total_effort':total_effort,'overall_ratio':Fraction(total_catch,total_effort),'scope':SCOPE}
