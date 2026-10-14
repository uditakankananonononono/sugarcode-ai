"""Microwave Engineering.

PARTIAL: caller real-resistance ideal reflection arithmetic only, not microwave
engineering, complex impedance analysis, measurement or hardware performance.
Positive resistances are caller inputs; frequency/material behavior not inferred.
"""
from fractions import Fraction
SCOPE='caller real-resistance reflection arithmetic only; no microwave hardware claims'


def reflection(loads,reference):
    """Loads exactlist/tuple1..64 exactint1..1000000;reference same range.
    Preserve input order; gamma=(load-reference)/(load+reference),return exact
    gamma,gamma squared,ideal1-gamma squared per load. No reactive components,
    lossy transmission, frequency dependence, VSWR measurements or certification.
    Repeated loads allowed. Reference supplied by caller,not assumed50 ohms.
    """
    if type(reference) is not int or not 1<=reference<=1000000:raise ValueError('reference must be exactint1..1000000')
    if type(loads) not in (list,tuple) or not 1<=len(loads)<=64:raise ValueError('loads must be exactlist/tuple length1..64')
    result=[]
    for load in loads:
        if type(load) is not int or not 1<=load<=1000000:raise ValueError('load must be exactint1..1000000')
        gamma=Fraction(load-reference,load+reference);squared=gamma*gamma;result.append((gamma,squared,1-squared))
    return {'reflection':tuple(result),'scope':SCOPE}
