"""Doc row1756 Critical Race Theory: PARTIAL supplied category outcome ledger.

Groups exact list2..20 (id,positive,total) tuples; unique exact nonblank str IDs
1..80; positive exact int0..1000, total exact int1..1000, positive<=total. Return
exact observed fractions and max-min rate gap. No inferred race, discrimination,
causality, significance, fairness or critical race theory validity.
"""
from fractions import Fraction


def compare_rates(groups):
    if type(groups) is not list or not 2<=len(groups)<=20:raise ValueError('groups must be an exact list with 2..20 entries')
    ids=set()
    for row in groups:
        if type(row) is not tuple or len(row)!=3:raise ValueError('group must be an id positive total tuple')
        name,positive,total=row
        if type(name) is not str or not 1<=len(name)<=80 or not name.strip() or name in ids:raise ValueError('group IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(name)
        if type(positive) is not int or not 0<=positive<=1000:raise ValueError('positive must be an integer in 0..1000')
        if type(total) is not int or not 1<=total<=1000:raise ValueError('total must be an integer in 1..1000')
        if positive>total:raise ValueError('positive must not exceed total')
    rates=[(n,Fraction(p,t)) for n,p,t in groups];gap=max(f for n,f in rates)-min(f for n,f in rates)
    return {'rates':[(n,(f.numerator,f.denominator)) for n,f in rates],'gap':(gap.numerator,gap.denominator),'claim':'PARTIAL','fairness_validated':False,'race_inferred':False}
