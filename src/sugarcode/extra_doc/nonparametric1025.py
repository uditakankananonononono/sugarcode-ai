"""Doc row1025 Nonparametric Methods: PARTIAL exact Mann-Whitney U fixture.

Two nonempty exact lists1..30 exact nonbool integers-1000..1000. Compute U for
left sample as pairwise left>right wins plus half a point for ties; return exact
rational pair and total cross-pair count. No p-value, assumptions or causal claim.
"""
from fractions import Fraction


def statistic(left,right):
    for sample in (left,right):
        if type(sample) is not list or not 1<=len(sample)<=30:
            raise ValueError('samples must be exact lists with 1..30 entries')
        if any(type(x) is not int or not -1000<=x<=1000 for x in sample):
            raise ValueError('sample values must be integers in -1000..1000')
    twice=sum(2 if a>b else 1 if a==b else 0 for a in left for b in right)
    u=Fraction(twice,2)
    return {'u':(u.numerator,u.denominator),'pairs':len(left)*len(right),
            'claim':'PARTIAL','assumptions_validated':False}
