"""Doc row1029 Multiple Imputation: PARTIAL exact Rubin pooling fixture.

Estimates/variances exact lists of same length2..20. Estimates nonbool integer
-1000..1000, variances nonbool int0..1000000. Return mean estimate,Qbar, within
variance Ubar, sample between variance B, total T=Ubar+(1+1/m)*B as rational
pairs. No imputation generation, valid model assumptions or confidence intervals.
"""
from fractions import Fraction


def pool(estimates,variances):
    if type(estimates) is not list or not 2<=len(estimates)<=20:
        raise ValueError('estimates must be an exact list with 2..20 entries')
    if any(type(x) is not int or not -1000<=x<=1000 for x in estimates):
        raise ValueError('estimates must be integers in -1000..1000')
    if type(variances) is not list or len(variances)!=len(estimates):
        raise ValueError('variances must be an exact list matching estimate count')
    if any(type(x) is not int or not 0<=x<=1000000 for x in variances):
        raise ValueError('variances must be integers in 0..1000000')
    m=len(estimates);mean=Fraction(sum(estimates),m);within=Fraction(sum(variances),m)
    between=sum((Fraction(x)-mean)**2 for x in estimates)/(m-1)
    total=within+(1+Fraction(1,m))*between
    pair=lambda x:(x.numerator,x.denominator)
    return {'mean':pair(mean),'within':pair(within),'between':pair(between),'total':pair(total),
            'claim':'PARTIAL','imputation_model_validated':False}
