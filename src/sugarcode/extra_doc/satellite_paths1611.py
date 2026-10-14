"""Satellite Communications.

PARTIAL: caller path-length propagation arithmetic only, not satellite
communications, ephemerides, visibility, link feasibility or actual latency.
Distances/speed supplied by caller;processing,queuing and geometry omitted.
"""
from fractions import Fraction
SCOPE='caller path-length propagation arithmetic only; no satellite visibility or link claims'


def delay(lengths,speed):
    """Lengths exactlist/tuple1..64 exactint0..1000000000000;speed exactint
    1..1000000000 in matching units. Return exact segment delays,total one-way
    and doubled total. No claim doubled total models a real return path.
    Preserve input order;zero segments allowed;no orbital or hardware inference.
    """
    if type(speed) is not int or not 1<=speed<=1000000000:raise ValueError('speed must be exactint1..1000000000')
    if type(lengths) not in (list,tuple) or not 1<=len(lengths)<=64:raise ValueError('lengths must be exactlist/tuple length1..64')
    parsed=[]
    for length in lengths:
        if type(length) is not int or not 0<=length<=1000000000000:raise ValueError('length must be exactint0..1000000000000')
        parsed.append(Fraction(length,speed))
    total=sum(parsed)
    return {'segment_delays':tuple(parsed),'one_way':total,'doubled':2*total,'scope':SCOPE}
