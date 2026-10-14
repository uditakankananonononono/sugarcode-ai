"""Atmospheric Chemistry.

PARTIAL: caller directed quantity-transfer ledger only, not atmospheric
chemistry, chemical reactions, kinetics, species identification or forecasting.
Caller labels are abstract buckets, not inferred molecular species.
"""
SCOPE='caller directed transfer ledger only; no atmospheric chemistry modeling'


def transfers(rows):
    """Exactlist/tuple1..64 triples(source,target,quantity);printable Unicode
    exactstr endpoint labels1..40,self-transfers allowed;exactint quantities
    0..1000000. Sorted(label,incoming,outgoing,net),total transferred and
    strictly net-positive labels. Mixedrows accepted. No reactions,units,
    stoichiometry,transport,rates or conservation of chemical species inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={};total=0
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        source,target,quantity=row
        if type(source) is not str or not 1<=len(source)<=40 or not all(ch.isprintable() for ch in source):raise ValueError('source must be exactstr printable Unicode length1..40')
        if type(target) is not str or not 1<=len(target)<=40 or not all(ch.isprintable() for ch in target):raise ValueError('target must be exactstr printable Unicode length1..40')
        if type(quantity) is not int or not 0<=quantity<=1000000:raise ValueError('quantity must be exactint0..1000000')
        incoming,outgoing=groups.get(source,(0,0));groups[source]=(incoming,outgoing+quantity)
        incoming,outgoing=groups.get(target,(0,0));groups[target]=(incoming+quantity,outgoing)
        total+=quantity
    result=tuple((label,incoming,outgoing,incoming-outgoing) for label,(incoming,outgoing) in sorted(groups.items()))
    return {'transfers':result,'total_transferred':total,'positive':tuple(row[0] for row in result if row[3]>0),'scope':SCOPE}
