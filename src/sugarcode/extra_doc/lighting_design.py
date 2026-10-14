"""Row 293 Lighting Design: exact finite inverse-square lighting selection.

Selects a subset of supplied point-light intensities to minimize squared error
from supplied illuminance targets at sample points, with a maximum-light cap.
Distances are supplied squared distances; attenuation is intensity/distance².
Enumerates at most 4096 subsets, returning exact sample illumination.
NOT_CLAIMED: perceptual mood validation, shadowing, surface normals, spectral
rendering, photometric calibration, aesthetic quality or physical deployment.
"""
from fractions import Fraction


def _number(v):
    if type(v) not in (int,Fraction):raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('values must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('values must fit 32 bits')
    return Fraction(v)


def select_lights(intensities,distance_squared,targets,max_lights):
    if any(type(v) not in (list,tuple) for v in (intensities,distance_squared,targets)):
        raise TypeError('inputs must be lists or tuples')
    n=len(intensities);m=len(targets)
    if not 1<=n<=12:raise ValueError('light count must be between 1 and 12')
    if not 1<=m<=8:raise ValueError('sample count must be between 1 and 8')
    if type(max_lights) is not int or not 0<=max_lights<=n:
        raise ValueError('max_lights must be a nonbool integer between zero and light count')
    if len(distance_squared)!=n or any(type(row) not in (list,tuple) or len(row)!=m for row in distance_squared):
        raise ValueError('distance matrix must match lights and samples')
    powers=[_number(v) for v in intensities];goals=[_number(v) for v in targets]
    distances=[[_number(v) for v in row] for row in distance_squared]
    if any(v<0 for v in powers+goals):raise ValueError('intensities and targets must be nonnegative')
    if any(v<=0 for row in distances for v in row):raise ValueError('squared distances must be positive')
    best=None;feasible=0
    for mask in range(1<<n):
        indices=[i for i in range(n) if mask&(1<<i)]
        if len(indices)>max_lights:continue
        feasible+=1
        illumination=[sum((powers[i]/distances[i][j] for i in indices),Fraction(0)) for j in range(m)]
        error=sum(((value-goal)**2 for value,goal in zip(illumination,goals)),Fraction(0))
        if best is None or error<best[0]:best=(error,indices,illumination)
    error,indices,illumination=best
    return {'selected_lights':indices,'illumination':illumination,'squared_error':error,
            'feasible_subset_count':feasible,'mood_validated':False}
