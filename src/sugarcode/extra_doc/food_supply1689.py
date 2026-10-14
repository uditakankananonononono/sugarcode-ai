"""Food Security.

PARTIAL: caller food supply/demand bucket arithmetic only, not food security,
nutritional adequacy, access assessment, food safety or distribution advice.
Caller quantities are abstract, not verified food availability or needs.
"""
SCOPE='caller food supply-demand bucket arithmetic only; no food security claims'


def allocations(rows):
    """Exactlist/tuple1..64 triples(label,supply,demand);unique printable Unicode
    exactstr labels1..40;exactint quantities0..1000000. Sorted(label,allocated,
    unmet,unused) with allocation=min(supply,demand),total unmet and unused,
    strictly unmet labels. Independent buckets only,no cross-bucket transfers.
    Mixedrows accepted;no prioritization,legal permissions or scarcity rules.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,supply,demand=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(supply) is not int or type(demand) is not int or not 0<=supply<=1000000 or not 0<=demand<=1000000:raise ValueError('quantities must be exactint0..1000000')
        allocated=min(supply,demand);parsed.append((label,allocated,demand-allocated,supply-allocated))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'allocations':result,'total_unmet':sum(row[2] for row in result),'total_unused':sum(row[3] for row in result),'unmet':tuple(row[0] for row in result if row[2]>0),'scope':SCOPE}
