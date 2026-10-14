"""Sustainable Diets.

PARTIAL: caller food-quantity/impact-factor products only, not sustainable
diets, nutrition, health, lifecycle assessment or dietary recommendations.
Caller factors are abstract, not verified food or environmental impact data.
"""
SCOPE='caller food-quantity-impact-factor products only; no sustainable diet advice'


def impacts(rows):
    """Exactlist/tuple1..64 triples(label,quantity,factor);printable Unicode exactstr
    labels1..40,repeats aggregate;exactint quantities0..1000000. Sorted(label,
    quantity sum,sum quantity*factor),total impact and strictly positive-impact labels.
    Mixedrows accepted;no units,verified factors,nutritional adequacy or outcomes.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,quantity,factor=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(quantity) is not int or type(factor) is not int or not 0<=quantity<=1000000 or not 0<=factor<=1000000:raise ValueError('quantities must be exactint0..1000000')
        old_quantity,old_impact=groups.get(label,(0,0));groups[label]=(old_quantity+quantity,old_impact+quantity*factor)
    result=tuple((label,quantity,impact) for label,(quantity,impact) in sorted(groups.items()))
    return {'impacts':result,'total_impact':sum(row[2] for row in result),'positive':tuple(row[0] for row in result if row[2]>0),'scope':SCOPE}
