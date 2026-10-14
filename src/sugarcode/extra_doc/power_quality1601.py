"""Power Quality.

PARTIAL: caller harmonic-amplitude ratio arithmetic only, not power-quality
measurement, electrical compliance, transient analysis or equipment safety.
Amplitudes supplied by caller; no waveform sampling, hardware or limits inferred.
"""
from fractions import Fraction
from math import isfinite
SCOPE='caller harmonic squared-ratio arithmetic only; no electrical compliance or safety'


def harmonics(values):
    """Exactlist/tuple1..64 nonnegative finite exactbuilt-in int/float0..1000000
    amplitudes: first=fundamental strictly positive,remaining higher harmonics.
    Fraction decimal spelling. Return squared fundamental,harmonic squared sum,
    squared THD ratio=sum higher squares/fundamental square and harmonic energy
    fraction=sum higher squares/sum all squares. No square root or RMS inference.
    """
    if type(values) not in (list,tuple) or not 1<=len(values)<=64:raise ValueError('values must be exactlist/tuple length1..64')
    parsed=[]
    for value in values:
        if type(value) not in (int,float) or not 0<=value<=1000000 or not isfinite(value):raise ValueError('amplitude must be finite built-in real0..1000000')
        parsed.append(Fraction(str(value)))
    if parsed[0]==0:raise ValueError('fundamental must be positive')
    fundamental=parsed[0]*parsed[0];higher=sum(value*value for value in parsed[1:])
    return {'fundamental_squared':fundamental,'harmonic_squared_sum':higher,
            'thd_squared':higher/fundamental,'harmonic_energy_fraction':higher/(fundamental+higher),'scope':SCOPE}
