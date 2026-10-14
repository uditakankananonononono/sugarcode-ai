"""Row 313 Sound Installation Design: bounded spatial audio-zone gain design.

Computes exact normalized inverse-squared-distance speaker gains at supplied
listener sample locations, avoiding zero distance with a positive floor.
Each listener's gains sum to one; this creates a spatial gain configuration.
NOT_CLAIMED: acoustic immersion validation, HRTF, room reflections, delay,
physical calibration, playback, artistic quality or deployment.
"""
from fractions import Fraction


def _number(v):
    if type(v) not in (int,Fraction):raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('values must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('values must fit 32 bits')
    return Fraction(v)


def spatial_gains(speakers,listeners,distance_floor=1):
    if type(speakers) not in (list,tuple) or type(listeners) not in (list,tuple):
        raise TypeError('speakers and listeners must be lists or tuples')
    if not 1<=len(speakers)<=8:raise ValueError('speaker count must be between 1 and 8')
    if not 1<=len(listeners)<=32:raise ValueError('listener count must be between 1 and 32')
    for position in list(speakers)+list(listeners):
        if type(position) not in (list,tuple) or len(position)!=3:
            raise ValueError('positions must have three coordinates')
    ss=[[_number(v) for v in row] for row in speakers];ls=[[_number(v) for v in row] for row in listeners]
    floor=_number(distance_floor)
    if floor<=0:raise ValueError('distance_floor must be positive')
    distances=[];gains=[]
    for listener in ls:
        ds=[sum(((a-b)**2 for a,b in zip(listener,speaker)),Fraction(0)) for speaker in ss]
        raw=[1/max(floor,d) for d in ds];total=sum(raw,Fraction(0))
        distances.append(ds);gains.append([v/total for v in raw])
    return {'gains':gains,'squared_distances':distances,'immersion_validated':False}
