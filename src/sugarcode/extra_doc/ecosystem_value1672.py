"""Ecosystem Services.

PARTIAL: caller area/unit-value ledger only, not ecosystem services,
economic valuation, ecological modeling or environmental benefit assessment.
Caller compatible values are abstract, not verified market or ecosystem data.
"""
SCOPE='caller area-unit-value ledger only; no ecosystem valuation claims'


def values(rows):
    """Exactlist/tuple1..64 triples(label,area,unit value);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint quantities0..1000000.
    Sorted(label,total area,sum area*unit value),total value and zero-value
    labels. Mixedrows accepted;no currency,discounting,tradeoffs or actual
    ecosystem service benefit inferred from arithmetic products.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,area,unit_value=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(area) is not int or type(unit_value) is not int or not 0<=area<=1000000 or not 0<=unit_value<=1000000:raise ValueError('quantities must be exactint0..1000000')
        old_area,old_value=groups.get(label,(0,0));groups[label]=(old_area+area,old_value+area*unit_value)
    result=tuple((label,area,value) for label,(area,value) in sorted(groups.items()))
    return {'values':result,'total_value':sum(row[2] for row in result),'zero_value':tuple(row[0] for row in result if row[2]==0),'scope':SCOPE}
