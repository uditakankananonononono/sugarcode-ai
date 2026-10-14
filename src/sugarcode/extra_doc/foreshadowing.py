"""Row 266, Foreshadowing Placement: analysis of planted hints (exact).

A story has n scenes numbered 1..n and the reveal happens in scene `reveal`. Each
hint is (scene, salience) with salience in (0, 1] = chance a reader notices it
(hints are independent). Reported, all exact:
- valid: every hint is in a scene strictly before the reveal (and at least 1);
- late_hints: indexes of hints placed at or after the reveal;
- notice_probability = 1 - prod (1 - salience_i): chance the reader notices at
  least one hint;
- subtle: every salience <= max_salience (caller supplied) while the hints as a
  whole are noticeable with probability >= min_notice (caller supplied);
- gaps: scene distances between consecutive hint scenes in order, starting from
  scene 0 and ending at the reveal, so a long silent stretch shows up.
Caps: 1 to 64 scenes, 0 to 8 hints, scene numbers nonbool ints, saliences and
thresholds nonbool int or Fraction with numerator and denominator at most 32 bits,
thresholds in [0, 1]. Order of checks: container types and counts first (at most a few
hundred cheap element type checks), then value conversion and range checks, and
only then any arithmetic on the values.

NOT_CLAIMED: scores numbers the caller supplies. It reads no story text, does not
judge whether a hint is actually subtle or good writing, generates no hints, and
renders nothing visual. No clinical or wet-lab claim.
"""
from fractions import Fraction

MAX_SCENES, MAX_HINTS = 64, 8


def _q(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return f


def place_hints(n_scenes, reveal, hints, max_salience, min_notice):
    if type(n_scenes) is not int or type(reveal) is not int:
        raise TypeError('n_scenes and reveal must be nonbool ints')
    if not 1 <= n_scenes <= MAX_SCENES:
        raise ValueError('n_scenes must be between 1 and 64')
    if not 1 <= reveal <= n_scenes:
        raise ValueError('reveal must be between 1 and n_scenes')
    if type(hints) not in (list, tuple):
        raise TypeError('hints must be a list or tuple of pairs')
    if len(hints) > MAX_HINTS:
        raise ValueError('at most 8 hints')
    for h in hints:
        if type(h) not in (list, tuple) or len(h) != 2:
            raise TypeError('each hint must be a pair (scene, salience)')
        if type(h[0]) is not int:
            raise TypeError('hint scenes must be nonbool ints')
        if not 1 <= h[0] <= n_scenes:
            raise ValueError('hint scene out of range')
    sal = [_q(h[1]) for h in hints]
    ms, mn = _q(max_salience), _q(min_notice)
    if any(not 0 < s <= 1 for s in sal):
        raise ValueError('salience must be in (0, 1]')
    if not (0 <= ms <= 1 and 0 <= mn <= 1):
        raise ValueError('thresholds must be in [0, 1]')
    scenes = [h[0] for h in hints]
    late = [i for i, s in enumerate(scenes) if s >= reveal]
    miss = Fraction(1)
    for s in sal:
        miss *= 1 - s
    notice = 1 - miss
    order = sorted(scenes)
    marks = [0] + order + [reveal]
    gaps = [marks[i + 1] - marks[i] for i in range(len(marks) - 1)]
    subtle = all(s <= ms for s in sal) and notice >= mn
    return {'valid': not late, 'late_hints': late, 'notice_probability': notice,
            'subtle': subtle, 'gaps': gaps}
