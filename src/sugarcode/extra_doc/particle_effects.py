"""Row 299 Particle Effects: exact bounded ballistic particle snapshots.

Generates position and velocity snapshots under constant supplied acceleration
for up to 32 particles and 64 sample times. Closed-form motion avoids numerical
integration drift; particle identity and chronological sample order are kept.
NOT_CLAIMED: rendered effects, collisions, fluid dynamics, stochastic emission,
perceptual quality, physical actuation or autonomous deployment.
"""
from fractions import Fraction


def _number(v):
    if type(v) not in (int,Fraction):raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('values must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('values must fit 32 bits')
    return Fraction(v)


def ballistic_particles(positions,velocities,acceleration,times):
    if any(type(v) not in (list,tuple) for v in (positions,velocities,acceleration,times)):
        raise TypeError('inputs must be lists or tuples')
    n=len(positions)
    if not 1<=n<=32:raise ValueError('particle count must be between 1 and 32')
    if not 1<=len(times)<=64:raise ValueError('time count must be between 1 and 64')
    if len(velocities)!=n:raise ValueError('velocity count must match particles')
    if len(acceleration)!=3:raise ValueError('vectors must have three coordinates')
    if any(type(row) not in (list,tuple) or len(row)!=3 for row in list(positions)+list(velocities)):
        raise ValueError('vectors must have three coordinates')
    ps=[[_number(v) for v in row] for row in positions];vs=[[_number(v) for v in row] for row in velocities]
    acc=[_number(v) for v in acceleration];ts=[_number(t) for t in times]
    if any(t<0 for t in ts):raise ValueError('times must be nonnegative')
    if any(a>=b for a,b in zip(ts,ts[1:])):raise ValueError('times must be strictly increasing')
    frames=[]
    for t in ts:
        p=[[x+v*t+a*t*t/2 for x,v,a in zip(row,vel,acc)] for row,vel in zip(ps,vs)]
        v=[[x+a*t for x,a in zip(row,acc)] for row in vs]
        frames.append({'time':t,'positions':p,'velocities':v})
    return {'frames':frames,'particle_count':n,'rendered':False}
