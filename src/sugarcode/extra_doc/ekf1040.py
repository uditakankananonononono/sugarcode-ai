"""Doc row1040 Extended Kalman Filters: PARTIAL scalar squared-measurement step.

mean/measurement exact ints-100..100, variance int0..100,noise int1..100,
nonbool exact types. h(x)=x²,J=2x; gain=P*J/(J²P+R), posterior=x+K(z-x²),
variance=(1-KJ)P. Exact rational output. No process prediction, convergence,
linearization adequacy or actual model validity claim.
"""
from fractions import Fraction


def update(mean,variance,measurement,noise):
    if any(type(x) is not int or not -100<=x<=100 for x in (mean,measurement)):
        raise ValueError('mean and measurement must be integers in -100..100')
    if type(variance) is not int or not 0<=variance<=100:
        raise ValueError('variance must be an integer in 0..100')
    if type(noise) is not int or not 1<=noise<=100:
        raise ValueError('noise must be an integer in 1..100')
    jacobian=2*mean;gain=Fraction(variance*jacobian,jacobian*jacobian*variance+noise)
    posterior=mean+gain*(measurement-mean*mean);v=(1-gain*jacobian)*variance
    pair=lambda x:(x.numerator,x.denominator)
    return {'mean':pair(posterior),'variance':pair(v),'gain':pair(gain),'claim':'PARTIAL','linearization_validated':False}
