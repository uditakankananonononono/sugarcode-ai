"""Mitigation Strategies.

PARTIAL: caller option cost/value subset arithmetic only, not mitigation
strategies,emissions savings,financial evaluation or policy recommendations.
Costs/values/budget are abstract caller units,not verified impacts or spending.
"""
SCOPE='caller option cost/value subsets only; no mitigation impacts or policy advice'


def options(rows,budget):
    """Rows exactlist/tuple0..12(label,cost,value),unique printable Unicode
    exactstr1..40 labels;cost/value exactint0..1000000;budget exactint0..12000000.
    Return all budget-feasible(labeltuple,costsum,valuesum),lexical labeltuple
    order;best_value maximum sum and all ties (labeltuples). Empty subset included.
    No actual mitigation estimates,optimal policy or permission to spend.
    Mixedrows accepted;additivity/no interaction is only caller toy model.
    """
    if type(budget) is not int or not 0<=budget<=12000000:raise ValueError('budget must be exactint0..12000000')
    if type(rows) not in (list,tuple) or len(rows)>12:raise ValueError('rows must be exactlist/tuple atmost12')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,cost,value=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(cost) is not int or type(value) is not int or not 0<=cost<=1000000 or not 0<=value<=1000000:raise ValueError('cost and value must be exactint0..1000000')
        parsed.append((label,cost,value))
    parsed.sort(key=lambda row:row[0]);feasible=[]
    for mask in range(1<<len(parsed)):
        selected=[row for i,row in enumerate(parsed) if mask&(1<<i)];cost=sum(row[1] for row in selected)
        if cost<=budget:feasible.append((tuple(row[0] for row in selected),cost,sum(row[2] for row in selected)))
    feasible.sort();best=max(row[2] for row in feasible)
    return {'feasible':tuple(feasible),'best_value':best,'ties':tuple(row[0] for row in feasible if row[2]==best),'scope':SCOPE}
