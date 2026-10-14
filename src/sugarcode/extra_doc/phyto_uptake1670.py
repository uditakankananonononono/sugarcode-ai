"""Phytoremediation.

PARTIAL: caller biomass/concentration product ledger only, not phytoremediation,
plant uptake prediction, species selection, cleanup effectiveness or safety.
Caller compatible units are abstract, not measured contaminant uptake data.
"""
SCOPE='caller biomass-concentration product ledger only; no phytoremediation claims'


def uptake(rows):
    """Exactlist/tuple1..64 triples(label,biomass,concentration);printable
    Unicode exactstr labels1..40,repeated labels aggregate;exactint quantities
    0..1000000. Sorted(label,total biomass,sum biomass*concentration),total
    product and strictly positive-product labels. Mixedrows accepted;no unit
    conversion,bioavailability,translocation,growth or disposal rules inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,biomass,concentration=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(biomass) is not int or type(concentration) is not int or not 0<=biomass<=1000000 or not 0<=concentration<=1000000:raise ValueError('quantities must be exactint0..1000000')
        old_biomass,old_product=groups.get(label,(0,0));groups[label]=(old_biomass+biomass,old_product+biomass*concentration)
    result=tuple((label,biomass,product) for label,(biomass,product) in sorted(groups.items()))
    return {'uptake':result,'total_product':sum(row[2] for row in result),'positive':tuple(row[0] for row in result if row[2]>0),'scope':SCOPE}
