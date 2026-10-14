"""Doc row1026 Robust Statistics: PARTIAL exact median/MAD fixture.

Input exact list1..100 of nonbool integers-1000..1000. Median is middle sorted
value or average of two middles. MAD is median absolute distance from median,
without normal scaling. Output normalized rational pairs. No distribution,
resilience guarantee, inference, uncertainty or clinical interpretation claimed.
"""
from fractions import Fraction


def _median(values):
    ordered=sorted(values);n=len(ordered)
    return (ordered[(n-1)//2]+ordered[n//2])/2


def summarize(values):
    if type(values) is not list or not 1<=len(values)<=100:
        raise ValueError('values must be an exact list with 1..100 entries')
    if any(type(x) is not int or not -1000<=x<=1000 for x in values):
        raise ValueError('values must be integers in -1000..1000')
    median=_median([Fraction(x) for x in values])
    mad=_median([abs(Fraction(x)-median) for x in values])
    return {'median':(median.numerator,median.denominator),'mad':(mad.numerator,mad.denominator),
            'claim':'PARTIAL','distribution_validated':False}
