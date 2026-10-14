"""Row 333 Marine Design: exact rectangular-hull static buoyancy concept.

Computes draft, freeboard, displaced volume and reserve mass for a supplied
box hull and mass in uniform water. Reports whether a specified minimum
freeboard is met; exact Archimedes balance uses mass/density displacement.
NOT_CLAIMED: real hull hydrodynamics, stability, seaworthiness, structural
safety, wave behavior, fabrication readiness or physical deployment.
"""
from fractions import Fraction


def _number(v):
    if type(v) not in (int,Fraction):raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('values must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('values must fit 32 bits')
    return Fraction(v)


def box_hull(length,beam,depth,mass,water_density=1000,minimum_freeboard=0):
    l,b,d,m,rho,f=[_number(v) for v in (length,beam,depth,mass,water_density,minimum_freeboard)]
    if l<=0 or b<=0 or d<=0:raise ValueError('hull dimensions must be positive')
    if m<0:raise ValueError('mass must be nonnegative')
    if rho<=0:raise ValueError('water_density must be positive')
    if not 0<=f<=d:raise ValueError('minimum_freeboard must be between zero and hull depth')
    volume=m/rho;draft=volume/(l*b);freeboard=d-draft
    reserve=rho*l*b*(d-f)-m
    return {'displaced_volume':volume,'draft':draft,'freeboard':freeboard,
            'reserve_mass':reserve,'freeboard_requirement_met':reserve>=0,'seaworthiness_validated':False}
