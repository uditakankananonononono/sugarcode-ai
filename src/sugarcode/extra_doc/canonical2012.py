"""Chaos Theory (canonical2012): PARTIAL caller finite modular doubling orbit.

modulus exactint1..32,start exactint0..modulus-1. Mapstate(2*state)%modulus.
Returntransienttuple/cycletuple includingfirststateonce;firstrepeatstep;
initial-state-return period ifstartisoncycleelseNone. No continuouschaos,
Lyapunovexponent/physicalpredictionclaim. Validatemodulus thenstart.
"""
SCOPE='PARTIAL: caller finite modular doubling orbit transient, cycle and return period'
NOT_CLAIMED=('continuous chaos','Lyapunov exponent','physical prediction')


def orbit(modulus,start):
    if type(modulus) is not int or not 1<=modulus<=32:raise ValueError('modulus exact int1..32')
    if type(start) is not int or not 0<=start<modulus:raise ValueError('start exact int0..modulus-1')
    seen={};states=[];state=start
    while state not in seen:
        seen[state]=len(states);states.append(state);state=(2*state)%modulus
    first=seen[state];transient=tuple(states[:first]);cycle=tuple(states[first:])
    return {'transient':transient,'cycle':cycle,'first_repeat_step':len(states),'return_period':len(cycle) if not transient else None,'chaos_validated':False}
