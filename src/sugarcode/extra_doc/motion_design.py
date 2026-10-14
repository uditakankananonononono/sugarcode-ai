"""Row 290 Motion Design: bounded purposeful quintic transition trajectory.

Generates exact rational position, velocity and acceleration samples for a
supplied one-dimensional transition. Quintic easing has zero endpoint speed
and acceleration. Exact peak speed=15*distance/(8*duration); conservative
acceleration bound=6*distance/duration². Reduced motion emits a static target.
NOT_CLAIMED: rendered animation, perceptual quality, accessibility certification,
physical actuation, arbitrary multidimensional choreography or deployment.
"""
from fractions import Fraction


def _number(v):
    if type(v) not in (int,Fraction):raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('values must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('values must fit 32 bits')
    return Fraction(v)


def design_motion(start,end,duration,samples=17,reduced_motion=False):
    if type(samples) is not int or not 2<=samples<=257:
        raise ValueError('samples must be a nonbool integer between 2 and 257')
    if type(reduced_motion) is not bool:raise TypeError('reduced_motion must be bool')
    a=_number(start);b=_number(end);t=_number(duration)
    if t<=0:raise ValueError('duration must be positive')
    if reduced_motion:
        return {'frames':[{'time':Fraction(0),'position':b,'velocity':Fraction(0),'acceleration':Fraction(0)}],
                'peak_speed':Fraction(0),'acceleration_bound':Fraction(0),'mode':'static','rendered':False}
    delta=b-a;frames=[]
    for i in range(samples):
        s=Fraction(i,samples-1)
        ease=10*s**3-15*s**4+6*s**5
        speed=30*s**2*(1-s)**2
        acceleration=60*s*(1-s)*(1-2*s)
        frames.append({'time':s*t,'position':a+delta*ease,
                       'velocity':delta*speed/t,'acceleration':delta*acceleration/t**2})
    return {'frames':frames,'peak_speed':Fraction(15,8)*abs(delta)/t,
            'acceleration_bound':6*abs(delta)/t**2,'mode':'quintic','rendered':False}
