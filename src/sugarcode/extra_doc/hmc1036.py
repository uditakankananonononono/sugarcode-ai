"""Doc row1036 Hamiltonian Monte Carlo: PARTIAL exact harmonic leapfrog fixture.

Position/momentum exact ints-100..100; step exact fraction tuple(num,den), ints
1<=num<=den<=100; steps exact int1..20. Harmonic U(q)=q²/2, unit mass. Apply
half momentum, full position, half momentum each step; return rational final
coordinates and energy difference. No sampling, acceptance, inference or mixing.
"""
from fractions import Fraction


def integrate(position,momentum,step,steps):
    if any(type(x) is not int or not -100<=x<=100 for x in (position,momentum)):
        raise ValueError('coordinates must be exact integers in -100..100')
    if type(step) is not tuple or len(step)!=2 or any(type(x) is not int for x in step) or not 1<=step[0]<=step[1]<=100:
        raise ValueError('step must be an exact integer fraction with 1<=num<=den<=100')
    if type(steps) is not int or not 1<=steps<=20:
        raise ValueError('steps must be an integer in 1..20')
    q,p=Fraction(position),Fraction(momentum);h=Fraction(*step);initial=(q*q+p*p)/2
    for _ in range(steps):
        p-=h*q/2;q+=h*p;p-=h*q/2
    delta=(q*q+p*p)/2-initial;pair=lambda x:(x.numerator,x.denominator)
    return {'position':pair(q),'momentum':pair(p),'energy_delta':pair(delta),
            'claim':'PARTIAL','sampling_validated':False}
