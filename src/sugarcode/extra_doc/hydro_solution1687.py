"""Hydroponics.

PARTIAL: caller solution/solute mass fraction ledger only, not hydroponics,
nutrient suitability, plant health, solution chemistry or growing advice.
Caller compatible masses are abstract, not verified nutrient measurements.
"""
from fractions import Fraction
SCOPE='caller solution-solute mass fraction ledger only; no hydroponics advice'


def fractions(rows):
    """Exactlist/tuple1..64 triples(label,solution,solute);printable Unicode exactstr
    labels1..40,repeated labels aggregate;exactint0<=solute<=solution<=1000000.
    Sorted(label,solution total,solute total,carrier,solute/solution or None at zero solution),total
    carrier and aggregate solute mass fraction. Mixedrows accepted.
    No nutrient sufficiency,pH,conductivity or plant growth conclusions.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,solution,solute=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(solution) is not int or type(solute) is not int or not 0<=solute<=solution<=1000000:raise ValueError('masses must be exactint0<=solute<=solution<=1000000')
        old_solution,old_solute=groups.get(label,(0,0));groups[label]=(old_solution+solution,old_solute+solute)
    result=tuple((label,solution,solute,solution-solute,Fraction(solute,solution) if solution else None) for label,(solution,solute) in sorted(groups.items()))
    total_carrier=sum(row[3] for row in result);total_solution=sum(row[1] for row in result);total_solute=sum(row[2] for row in result)
    return {'fractions':result,'total_carrier':total_carrier,'solute_fraction':Fraction(total_solute,total_solution) if total_solution else None,'scope':SCOPE}
