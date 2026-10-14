"""Adaptation Planning.

PARTIAL: caller rectangular option/scenario cost regret arithmetic only, not
adaptation planning,climate risks,economic evaluation or policy advice. Costs
are abstract caller integers,not validated impacts,probabilities or preferences.
"""
SCOPE='caller scenario cost regret arithmetic only; no climate adaptation or policy advice'


def regret(rows):
    """Exactlist/tuple1..32 rows(label,costs),unique printable Unicode exactstr
    label1..40;costs exactlist/tuple1..32 exactint0..1000000,equal widths. Lower
    costs preferred by caller model. For each scenario subtract column minimum,
    return sorted(label,regret tuple,worst regret),minimax value and all tied
    labels. No probabilities,expected utilities or actual recommendations.
    Mixedrows accepted;rectangular matrix dimensions caller-defined.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=32:raise ValueError('rows must be exactlist/tuple length1..32')
    labels=set();parsed=[];width=None
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=2:raise ValueError('row must be exactlist/tuple pair')
        label,costs=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(costs) not in (list,tuple) or not 1<=len(costs)<=32:raise ValueError('costs must be exactlist/tuple length1..32')
        for cost in costs:
            if type(cost) is not int or not 0<=cost<=1000000:raise ValueError('cost must be exactint0..1000000')
        if width is None:width=len(costs)
        elif len(costs)!=width:raise ValueError('cost vectors must have equal width')
        parsed.append((label,tuple(costs)))
    minima=tuple(min(costs[i] for _,costs in parsed) for i in range(width));result=[]
    for label,costs in sorted(parsed,key=lambda row:row[0]):
        regrets=tuple(cost-minimum for cost,minimum in zip(costs,minima));result.append((label,regrets,max(regrets)))
    minimax=min(row[2] for row in result)
    return {'regrets':tuple(result),'minimax':minimax,'ties':tuple(row[0] for row in result if row[2]==minimax),'scope':SCOPE}
