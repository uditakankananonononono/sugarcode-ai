"""Cleaner Production.

PARTIAL: caller resource/output intensity arithmetic only, not cleaner
production, environmental improvement, process optimization or certification.
Caller quantities are abstract, not verified production or resource-use data.
"""
from fractions import Fraction
SCOPE='caller resource-output intensity arithmetic only; no cleaner production claims'


def intensity(rows):
    """Exactlist/tuple1..64 triples(label,resource,output);printable Unicode
    exactstr labels1..40,repeats aggregate;exactint resource0..1000000,
    output1..1000000. Sorted(label,total resource,total output,intensity),total
    resource,output,aggregate intensity. Mixedrows accepted;no units,
    comparability,efficiency benchmarks or actual environmental gain inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,resource,output=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(resource) is not int or type(output) is not int or not 0<=resource<=1000000 or not 1<=output<=1000000:raise ValueError('resource must be exactint0..1000000 and output exactint1..1000000')
        old_resource,old_output=groups.get(label,(0,0));groups[label]=(old_resource+resource,old_output+output)
    result=tuple((label,resource,output,Fraction(resource,output)) for label,(resource,output) in sorted(groups.items()))
    resource=sum(row[1] for row in result);output=sum(row[2] for row in result)
    return {'intensity':result,'resource':resource,'output':output,'aggregate_intensity':Fraction(resource,output),'scope':SCOPE}
