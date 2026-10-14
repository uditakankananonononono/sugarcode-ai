"""Doc row1024 Permutation Testing: PARTIAL exact fixed-size label test.

values exact list2..12 nonbool ints-100..100; split exact int1..len-1. Observed
first split items versus remainder. Statistic absolute mean difference. Enumerate
all fixed-size index subsets, including repeated values as distinct observations;
p fraction is count of stats >= observed divided by subset count. No valid design,
exchangeability, causality or actual inference assumptions claimed.
"""
from fractions import Fraction
from itertools import combinations


def test(values,split):
    if type(values) is not list or not 2<=len(values)<=12:
        raise ValueError('values must be an exact list with 2..12 entries')
    if any(type(x) is not int or not -100<=x<=100 for x in values):
        raise ValueError('values must be integers in -100..100')
    if type(split) is not int or not 1<=split<len(values):
        raise ValueError('split must be an integer in 1..len(values)-1')
    def statistic(indices):
        group=sum(values[i] for i in indices)
        return abs(Fraction(group,split)-Fraction(sum(values)-group,len(values)-split))
    observed=statistic(range(split));extreme=0;total=0
    for indices in combinations(range(len(values)),split):
        total+=1
        if statistic(indices)>=observed:extreme+=1
    p=Fraction(extreme,total)
    return {'p':(p.numerator,p.denominator),'extreme':extreme,'total':total,
            'claim':'PARTIAL','assumptions_validated':False}
