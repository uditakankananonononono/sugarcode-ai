"""Antenna Design.

PARTIAL: caller propagation-speed/frequency ideal length arithmetic only, not
antenna design, resonance prediction, impedance matching, radiation efficiency
or hardware validation. Speed/scale supplied by caller; no material constants.
"""
from fractions import Fraction
SCOPE='caller ideal wavelength-length arithmetic only; no antenna performance claims'


def lengths(frequencies,speed,numerator,denominator):
    """Frequencies exactlist/tuple1..64 unique exactint1..1000000000000;
    speed exactint1..1000000000;scale numerator/denominator exactint1..1000.
    Return frequency-sorted(freq,exact speed/freq wavelength,scaled length).
    Caller units must be compatible. Scale not inferred as optimal fraction.
    No impedance, geometry, bandwidth, safety or electromagnetic simulation.
    """
    if type(speed) is not int or not 1<=speed<=1000000000:raise ValueError('speed must be exactint1..1000000000')
    if type(numerator) is not int or type(denominator) is not int or not 1<=numerator<=1000 or not 1<=denominator<=1000:
        raise ValueError('scale components must be exactint1..1000')
    if type(frequencies) not in (list,tuple) or not 1<=len(frequencies)<=64:raise ValueError('frequencies must be exactlist/tuple length1..64')
    seen=set();result=[]
    for frequency in frequencies:
        if type(frequency) is not int or not 1<=frequency<=1000000000000:raise ValueError('frequency must be exactint1..1000000000000')
        if frequency in seen:raise ValueError('frequencies must be unique')
        seen.add(frequency);wavelength=Fraction(speed,frequency);result.append((frequency,wavelength,wavelength*Fraction(numerator,denominator)))
    return {'lengths':tuple(sorted(result)),'scope':SCOPE}
