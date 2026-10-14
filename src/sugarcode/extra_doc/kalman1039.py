"""Doc row1039 Kalman Filters: PARTIAL exact scalar measurement update.

mean/measurement exact ints-1000..1000,variance exact int0..1000,noise exact
int1..1000. K=variance/(variance+noise), posterior=mean+K*(measurement-mean),
posterior variance=(1-K)*variance. Rational pairs output. No time prediction,
noise estimation, distribution/model validity or actual tracking claim.
"""
from fractions import Fraction


def update(mean,variance,measurement,noise):
    if any(type(x) is not int or not -1000<=x<=1000 for x in (mean,measurement)):
        raise ValueError('mean and measurement must be integers in -1000..1000')
    if type(variance) is not int or not 0<=variance<=1000:
        raise ValueError('variance must be an integer in 0..1000')
    if type(noise) is not int or not 1<=noise<=1000:
        raise ValueError('noise must be an integer in 1..1000')
    gain=Fraction(variance,variance+noise);posterior=mean+gain*(measurement-mean);v=(1-gain)*variance
    pair=lambda x:(x.numerator,x.denominator)
    return {'mean':pair(posterior),'variance':pair(v),'gain':pair(gain),'claim':'PARTIAL','model_validated':False}
