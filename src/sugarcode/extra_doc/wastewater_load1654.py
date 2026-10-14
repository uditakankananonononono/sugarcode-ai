"""Wastewater Treatment.

PARTIAL: caller flow/concentration load ledger only, not wastewater treatment,
plant design, pollutant testing, discharge compliance or environmental advice.
No unit conversion, removal efficiency or regulatory limit is inferred.
"""
SCOPE='caller flow-concentration load ledger only; no wastewater compliance claims'


def loads(rows):
    """Exactlist/tuple1..64 triples(label,flow,concentration);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint quantities0..1000000.
    Sorted(label,total flow,sum flow*concentration),total load and zero-flow
    labels. Product uses caller compatible units only. Mixedrows accepted.
    No categorical safe/unsafe classifications or treatment operations.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,flow,concentration=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(flow) is not int or type(concentration) is not int or not 0<=flow<=1000000 or not 0<=concentration<=1000000:raise ValueError('quantities must be exactint0..1000000')
        old_flow,old_load=groups.get(label,(0,0));groups[label]=(old_flow+flow,old_load+flow*concentration)
    result=tuple((label,flow,load) for label,(flow,load) in sorted(groups.items()))
    return {'loads':result,'total_load':sum(row[2] for row in result),'zero_flow':tuple(row[0] for row in result if row[1]==0),'scope':SCOPE}
