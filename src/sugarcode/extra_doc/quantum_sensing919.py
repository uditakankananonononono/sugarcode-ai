"""Quantum Sensing - Ultra-precise measurement.

Bounded implementation: classical exact-form Ramsey/Bernoulli count inference on a caller-chosen
monotone phase branch. Not a physical sensor, quantum advantage or a guarantee of
ultra-precise measurement. Binomial uncertainty ignores technical noise.
"""
from math import acos, sqrt, isfinite


def ramsey_estimate(ones, shots, interrogation=1.0, contrast=1.0, z=1.959963984540054):
    """Estimate nonnegative frequency on phase in [0,pi] with Wilson interval.

    P(1)=(1-contrast*cos(frequency*interrogation))/2. Invert observed proportion
    after clipping to the model's physical range. Wilson probability interval is
    clipped likewise before inversion. Branch and contrast must be supplied;
    there is no sign or phase-wrap identification. Fisher information is evaluated
    at the estimate and may be zero at a contrast<1 endpoint.
    """
    for value in (ones,shots):
        if type(value) is not int:
            raise ValueError('counts must be built-in ints')
    if not 1<=shots<=10**12 or not 0<=ones<=shots:
        raise ValueError('require 1<=shots<=10^12 and 0<=ones<=shots')
    for value in (interrogation,contrast,z):
        if type(value) not in (int,float) or abs(value)>1e20 or not isfinite(value):
            raise ValueError('finite built-in real parameters required')
    if not 1e-12<=interrogation<=1e12 or not 0<contrast<=1 or not 0<z<=10:
        raise ValueError('interrogation, contrast or z outside range')
    p=ones/shots
    denom=1+z*z/shots
    center=(p+z*z/(2*shots))/denom
    half=z*sqrt(p*(1-p)/shots+z*z/(4*shots*shots))/denom
    low=max(0,center-half);high=min(1,center+half)
    def invert(probability):
        cosine=max(-1,min(1,(1-2*probability)/contrast))
        return acos(cosine)/interrogation
    estimate=invert(p)
    lo,hi=invert(low),invert(high)
    model_p=max((1-contrast)/2,min((1+contrast)/2,p))
    cosphase=max(-1,min(1,(1-2*model_p)/contrast))
    information=(interrogation**2 if contrast==1 else
                 contrast**2*interrogation**2*(1-cosphase*cosphase)/(4*model_p*(1-model_p)))
    return {'frequency':estimate,'frequency_interval':(lo,hi),
            'observed_probability':p,'wilson_probability_interval':(low,high),
            'fisher_information_per_shot':information,'clipped':p!=model_p,
            'scope':'monotone Ramsey phase branch; binomial sampling uncertainty only'}
