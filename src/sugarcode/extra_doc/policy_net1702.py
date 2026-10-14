"""Environmental Policy.

PARTIAL: caller cost/benefit ledger arithmetic only, not environmental policy,
policy effectiveness, environmental benefit valuation or legal advice.
Caller compatible values are abstract, not verified public-policy outcomes.
"""
SCOPE='caller cost-benefit ledger arithmetic only; no environmental policy advice'


def net(rows):
    """Exactlist/tuple1..64 triples(label,cost,benefit);printable Unicode
    exactstr labels1..40,repeats aggregate;exactint values0..1000000. Sorted
    (label,cost sum,benefit sum,benefit-cost),total net and strictly positive
    labels. Mixedrows accepted;no currency,discounting,legal status,causality,
    public preferences or actual environmental outcomes inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,cost,benefit=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(cost) is not int or type(benefit) is not int or not 0<=cost<=1000000 or not 0<=benefit<=1000000:raise ValueError('values must be exactint0..1000000')
        old_cost,old_benefit=groups.get(label,(0,0));groups[label]=(old_cost+cost,old_benefit+benefit)
    result=tuple((label,cost,benefit,benefit-cost) for label,(cost,benefit) in sorted(groups.items()))
    return {'net':result,'total_net':sum(row[3] for row in result),'positive':tuple(row[0] for row in result if row[3]>0),'scope':SCOPE}
