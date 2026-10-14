"""Row 579, Audio Engine (PARTIAL: one exact step of an audio engine): mix 16-bit sample tracks with gains.

mix_pcm(tracks, gains) mixes up to 4 tracks of equal length. For each position i the exact mix is the sum over tracks
of gains[t] * tracks[t][i] (a Fraction); the output sample is that value rounded half up (floor(value + 1/2)) and then
clamped into the 16-bit range -32768 to 32767. It returns:
  samples   the output integers;
  exact     the unrounded exact mixes (Fractions);
  clipped   how many positions the clamp changed (rounded value outside the 16-bit range);
  peak      the largest absolute exact mix (a Fraction).
Caps: tracks is a list or tuple of 1 to 4 tracks; each track is a list or tuple of 1 to 64 nonbool ints from -32768 to
32767, and all tracks have the same length; gains is a list or tuple with one gain per track, each a nonbool int or
Fraction with 32-bit numerator and denominator, from 0 to 4.
Order of checks: tracks type, track count, then each track in order (type, length 1 to 64, same length as the first,
then each sample's type and range in position order), then gains (type, count equal to tracks, then each gain's
type, 32 bits and range in order), and only then any arithmetic.

NOT_CLAIMED: this is one integer mixing rule. It is not an audio engine: no sample rate, filtering, delay, pan,
dither, noise shaping, resampling, file formats, or playback, and it says nothing about how the result sounds.
No clinical or wet-lab claim.
"""
from fractions import Fraction
from math import floor

LOW, HIGH = -32768, 32767
MAX_TRACKS = 4
MAX_LEN = 64
MAX_GAIN = 4


def _seq(v, what):
    if type(v) not in (list, tuple):
        raise TypeError(what + ' must be a list or tuple')
    return v


def mix_pcm(tracks, gains):
    ts = _seq(tracks, 'tracks')
    if not 1 <= len(ts) <= MAX_TRACKS:
        raise ValueError('track count must be between 1 and 4')
    rows = []
    for t in ts:
        row = _seq(t, 'track')
        if not 1 <= len(row) <= MAX_LEN:
            raise ValueError('track length must be between 1 and 64')
        if rows and len(row) != len(rows[0]):
            raise ValueError('all tracks must have the same length')
        for s in row:
            if type(s) is not int:
                raise TypeError('sample must be a nonbool int')
            if not LOW <= s <= HIGH:
                raise ValueError('sample must be between -32768 and 32767')
        rows.append(row)
    gs = _seq(gains, 'gains')
    if len(gs) != len(rows):
        raise ValueError('gains must have one entry per track')
    gl = []
    for g in gs:
        if type(g) not in (int, Fraction):
            raise TypeError('gain must be a nonbool int or Fraction')
        f = Fraction(g)
        if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
            raise ValueError('rational values must fit 32 bits')
        if not 0 <= f <= MAX_GAIN:
            raise ValueError('gain must be between 0 and 4')
        gl.append(f)
    exact = []
    out = []
    clipped = 0
    for i in range(len(rows[0])):
        v = sum(gl[k] * rows[k][i] for k in range(len(rows)))
        r = floor(v + Fraction(1, 2))
        c = min(HIGH, max(LOW, r))
        clipped += c != r
        exact.append(v)
        out.append(c)
    return {'samples': out, 'exact': exact, 'clipped': clipped, 'peak': max(abs(v) for v in exact)}
