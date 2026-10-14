"""Row 267, Tension Building: exact analysis of a scene-by-scene tension curve.

Input is a tension level per scene (nonneg ints or Fractions). Reported exactly:
- climax_scene: index (0-based) of the first maximum and climax_value;
- build: sum of the positive scene-to-scene rises, release: sum of the drops;
  so final = first + build - release;
- builds_to_climax: tension never falls before the climax scene;
- released_after_climax: some drop happens after the climax;
- release_fraction = (climax_value - last) / climax_value (0 when the climax is 0),
  how much tension the ending lets go of;
- reversals: number of direction changes over the whole curve (rise to drop or drop to rise, flat
  steps skipped);
- peaks: indexes of strict local peaks (interior points above both neighbours,
  plus an endpoint above its single neighbour).
Caps: 2 to 32 scenes, levels nonneg nonbool int or Fraction with numerator and
denominator at most 32 bits. Order of checks: container types and counts first (at most a few
hundred cheap element type checks), then value conversion and range checks, and
only then any arithmetic on the values.

NOT_CLAIMED: summarises numbers the caller supplies. It reads no story text, does
not generate or judge drama, and renders no chart or storyboard. No clinical or
wet-lab claim.
"""
from fractions import Fraction

MAX_SCENES = 32


def _q(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return f


def analyse_tension(levels):
    if type(levels) not in (list, tuple):
        raise TypeError('levels must be a list or tuple')
    n = len(levels)
    if not 2 <= n <= MAX_SCENES:
        raise ValueError('scene count must be between 2 and 32')
    t = [_q(v) for v in levels]
    if any(v < 0 for v in t):
        raise ValueError('levels must be non negative')
    climax = 0
    for i in range(1, n):
        if t[i] > t[climax]:
            climax = i
    d = [t[i + 1] - t[i] for i in range(n - 1)]
    build = sum((x for x in d if x > 0), Fraction(0))
    release = sum((-x for x in d if x < 0), Fraction(0))
    builds = all(x >= 0 for x in d[:climax])
    released = any(x < 0 for x in d[climax:])
    top = t[climax]
    frac = (top - t[-1]) / top if top != 0 else Fraction(0)
    signs = [(x > 0) - (x < 0) for x in d if x != 0]
    reversals = sum(1 for i in range(len(signs) - 1) if signs[i] != signs[i + 1])
    peaks = []
    for i in range(n):
        left = t[i] > t[i - 1] if i > 0 else True
        right = t[i] > t[i + 1] if i < n - 1 else True
        if left and right:
            peaks.append(i)
    return {'climax_scene': climax, 'climax_value': top, 'build': build, 'release': release,
            'builds_to_climax': builds, 'released_after_climax': released,
            'release_fraction': frac, 'reversals': reversals, 'peaks': peaks}
