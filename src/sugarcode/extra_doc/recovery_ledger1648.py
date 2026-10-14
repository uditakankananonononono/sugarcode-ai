"""Recycling.

PARTIAL: caller input/recovered quantity ledger only, not recycling operations,
material identification, contamination testing or recovery certification.
Recovered amounts are caller declarations, not verified recycling outcomes.
"""
from fractions import Fraction
SCOPE='caller input-recovered ledger only; no verified recycling claims'


def recovery(rows):
    """Exactlist/tuple1..64 triples(label,input,recovered);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint0<=recovered<=input
    <=1000000. Sorted(label,input sum,recovered sum,residual,recovered/input
    or None at zero input),total residual. Mixedrows accepted. No material
    eligibility, yield assumptions, environmental or financial benefit claims.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,quantity,recovered=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(quantity) is not int or type(recovered) is not int or not 0<=recovered<=quantity<=1000000:raise ValueError('quantities must be exactint0<=recovered<=input<=1000000')
        old_input,old_recovered=groups.get(label,(0,0));groups[label]=(old_input+quantity,old_recovered+recovered)
    result=tuple((label,quantity,recovered,quantity-recovered,Fraction(recovered,quantity) if quantity else None) for label,(quantity,recovered) in sorted(groups.items()))
    return {'recovery':result,'total_residual':sum(row[3] for row in result),'scope':SCOPE}
