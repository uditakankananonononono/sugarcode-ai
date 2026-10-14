"""Doc row1041 Unscented Kalman Filters: PARTIAL three-point square transform.

mean exact int-100..100, spread exact int1..100. Supplied prior sigma points
x,x-spread,x+spread, weights2/3,1/6,1/6. Transform h(x)=x² and report exact
weighted output mean/variance and input-output covariance. No filter update,
general UKF parameters, approximation accuracy or actual model validity claim.
"""
from fractions import Fraction


def transform(mean,spread):
    if type(mean) is not int or not -100<=mean<=100:
        raise ValueError('mean must be an integer in -100..100')
    if type(spread) is not int or not 1<=spread<=100:
        raise ValueError('spread must be an integer in 1..100')
    points=[mean,mean-spread,mean+spread];weights=[Fraction(2,3),Fraction(1,6),Fraction(1,6)]
    outputs=[x*x for x in points];average=sum(w*y for w,y in zip(weights,outputs))
    variance=sum(w*(y-average)**2 for w,y in zip(weights,outputs))
    cross=sum(w*(x-mean)*(y-average) for w,x,y in zip(weights,points,outputs))
    pair=lambda x:(x.numerator,x.denominator)
    return {'output_mean':pair(average),'output_variance':pair(variance),'cross_covariance':pair(cross),
            'claim':'PARTIAL','approximation_validated':False}
