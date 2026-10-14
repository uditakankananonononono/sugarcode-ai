"""Doc row1783 Poverty: PARTIAL supplied income-threshold shortfall fixture.

Incomes exact list1..100 (id,income) tuples, unique nonblank exact str1..80 IDs;
income exact int0..1000; line exact int1..1000. Return strict-below-line IDs,
shortfalls and exact mean normalized gap. No real poverty/household classification.
"""
from fractions import Fraction


def audit_gap(incomes,line):
    if type(incomes) is not list or not 1<=len(incomes)<=100:raise ValueError('incomes must be an exact list with 1..100 entries')
    ids=set()
    for row in incomes:
        if type(row) is not tuple or len(row)!=2:raise ValueError('income row must be an id income tuple')
        n,u=row
        if type(n) is not str or not 1<=len(n)<=80 or not n.strip() or n in ids:raise ValueError('IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(n)
        if type(u) is not int or not 0<=u<=1000:raise ValueError('income must be an integer in 0..1000')
    if type(line) is not int or not 1<=line<=1000:raise ValueError('line must be an integer in 1..1000')
    gaps=[(n,max(0,line-u)) for n,u in incomes];gap=Fraction(sum(g for n,g in gaps),len(incomes)*line)
    return {'below':[n for n,u in incomes if u<line],'shortfalls':gaps,'normalized_gap':(gap.numerator,gap.denominator),'claim':'PARTIAL','poverty_inferred':False}
