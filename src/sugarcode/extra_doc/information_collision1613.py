"""Information Theory.

PARTIAL: caller discrete count collision arithmetic only, not information-theory
coverage,Shannon entropy,source modeling or coding performance. Counts supplied
by caller; no statistical population or independence assumptions validated.
"""
from fractions import Fraction
SCOPE='caller discrete count collision arithmetic only; no source or coding performance claims'


def collision(counts):
    """Exactlist/tuple1..64 exactint0..1000000 counts with positive total.
    Return exact probability sum((count/total)^2),inverse collision probability,
    distinct positive-count categories,total count. Zero-count slots allowed.
    Probability assumes independent draws from caller empirical proportions,
    not finite-population draws without replacement. No entropy log calculation.
    """
    if type(counts) not in (list,tuple) or not 1<=len(counts)<=64:raise ValueError('counts must be exactlist/tuple length1..64')
    for count in counts:
        if type(count) is not int or not 0<=count<=1000000:raise ValueError('count must be exactint0..1000000')
    total=sum(counts)
    if total==0:raise ValueError('count total must be positive')
    probability=Fraction(sum(count*count for count in counts),total*total)
    return {'collision':probability,'inverse_collision':1/probability,'positive_categories':sum(count>0 for count in counts),'total':total,'scope':SCOPE}
