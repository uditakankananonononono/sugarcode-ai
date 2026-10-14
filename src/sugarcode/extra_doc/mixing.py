"""Row 306 Mixing: exact bounded weighted mono PCM mix and peak normalization.

Combines equal-length supplied signed-16-bit tracks using rational gains.
Optionally scales the full mix to a requested peak ceiling, preserving gain
ratios. Returns exact rational samples and unnormalized overload diagnostics.
NOT_CLAIMED: perceptual loudness balance, EQ/compression, stereo placement,
hardware playback, artistic quality, quantized audio export or deployment.
"""
from fractions import Fraction


def _gain(v):
    if type(v) not in (int,Fraction):raise TypeError('gains must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('gains must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('gains must fit 32 bits')
    if v<0:raise ValueError('gains must be nonnegative')
    return Fraction(v)


def mix_tracks(tracks,gains,peak_ceiling=32767,normalize=True):
    if type(tracks) not in (list,tuple) or type(gains) not in (list,tuple):
        raise TypeError('tracks and gains must be lists or tuples')
    if not 1<=len(tracks)<=8:raise ValueError('track count must be between 1 and 8')
    if len(gains)!=len(tracks):raise ValueError('gain count must match tracks')
    for track in tracks:
        if type(track) not in (list,tuple) or not 1<=len(track)<=4096:
            raise ValueError('tracks must have between 1 and 4096 samples')
    length=len(tracks[0])
    if any(len(track)!=length for track in tracks):raise ValueError('track lengths must agree')
    if type(peak_ceiling) is not int or not 1<=peak_ceiling<=32767:
        raise ValueError('peak_ceiling must be a nonbool integer between 1 and 32767')
    if type(normalize) is not bool:raise TypeError('normalize must be bool')
    if any(type(v) is not int or not -32768<=v<=32767 for track in tracks for v in track):
        raise ValueError('samples must be nonbool signed 16-bit integers')
    gs=[_gain(v) for v in gains]
    raw=[sum((track[i]*g for track,g in zip(tracks,gs)),Fraction(0)) for i in range(length)]
    peak=max(abs(v) for v in raw)
    scale=Fraction(peak_ceiling)/peak if normalize and peak>peak_ceiling else Fraction(1)
    mixed=[v*scale for v in raw]
    return {'samples':mixed,'raw_peak':peak,'scale':scale,'peak':max(abs(v) for v in mixed),
            'overload_indices':[i for i,v in enumerate(raw) if abs(v)>peak_ceiling],
            'perceptual_balance_validated':False}
