"""Brownfield Redevelopment.

PARTIAL: caller area/unit-cost/budget arithmetic only, not brownfield
redevelopment, land valuation, remediation planning or investment advice.
Caller quantities are declarations, not verified site conditions or quotes.
"""
SCOPE='caller area-unit-cost-budget arithmetic only; no brownfield redevelopment advice'


def budgets(rows):
    """Exactlist/tuple1..64 quads(label,area,unit cost,budget);unique printable
    Unicode exactstr labels1..40;exactint quantities0..1000000. Sorted(label,
    area*unit cost,budget-cost),strictly over-budget labels and total cost.
    Mixedrows accepted;no currency,permits,contamination or financing inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,area,unit_cost,budget=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(area) is not int or type(unit_cost) is not int or type(budget) is not int or not 0<=area<=1000000 or not 0<=unit_cost<=1000000 or not 0<=budget<=1000000:raise ValueError('quantities must be exactint0..1000000')
        cost=area*unit_cost;parsed.append((label,cost,budget-cost))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'budgets':result,'over_budget':tuple(row[0] for row in result if row[2]<0),'total_cost':sum(row[1] for row in result),'scope':SCOPE}
