"""Row 340 Narrative Design: finite story-beat to gameplay-encounter alignment (exact).

Each story beat has a caller-supplied target intensity and 1 to 4 candidate
gameplay encounters, each (intensity, minutes). One encounter is chosen per beat.
The mismatch of a beat is |encounter intensity - beat target|. The selection
minimizes total mismatch subject to total minutes <= minutes_budget; ties go to
fewer total minutes, then to the first candidate in option order.
Caps: 1 to 6 beats, 4 options each, 4096 candidates. Intensities and minutes are
nonnegative; target intensities, minutes and the budget are nonbool int or Fraction
(no float) with numerator and denominator at most 32 bits. All arithmetic is exact
(Fraction). Caps are implementation choices, not spec values.
Intensity values are numbers the caller supplies; nothing is read from text.
NOT_CLAIMED: story quality, emotional effect, pacing quality beyond this
intensity match, player engagement or enjoyment, narrative coherence or causality,
originality, accessibility, human playtesting, generation of story or gameplay
content, deployment.
"""
from fractions import Fraction
from itertools import product

NOT_CLAIMED = ('story quality', 'emotional effect', 'pacing quality beyond intensity match',
               'player engagement or enjoyment', 'narrative coherence or causality', 'originality',
               'accessibility', 'human playtesting', 'content generation', 'deployment')
MAX_BEATS = 6
MAX_OPTIONS = 4


def _number(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length() > 32:
            raise ValueError('values must fit 32 bits')
    elif v.numerator.bit_length() > 32 or v.denominator.bit_length() > 32:
        raise ValueError('values must fit 32 bits')
    return Fraction(v)


def align_story_gameplay(beats, minutes_budget):
    if type(beats) not in (list, tuple):
        raise TypeError('beats must be a list or tuple')
    if not 1 <= len(beats) <= MAX_BEATS:
        raise ValueError('beat count must be between 1 and 6')
    for beat in beats:
        if type(beat) not in (list, tuple) or len(beat) != 2:
            raise ValueError('each beat must be (target_intensity, options)')
        options = beat[1]
        if type(options) not in (list, tuple) or not 1 <= len(options) <= MAX_OPTIONS:
            raise ValueError('each beat must have between 1 and 4 encounter options')
        if any(type(o) not in (list, tuple) or len(o) != 2 for o in options):
            raise ValueError('options must contain intensity and minutes')
    budget = _number(minutes_budget)
    data = [(_number(b[0]), [(_number(o[0]), _number(o[1])) for o in b[1]]) for b in beats]
    if budget < 0:
        raise ValueError('minutes budget must be nonnegative')
    if any(t < 0 for t, _ in data) or any(i < 0 or m < 0 for _, opts in data for i, m in opts):
        raise ValueError('intensities and minutes must be nonnegative')
    best = None
    feasible = 0
    for idx in product(*(range(len(opts)) for _, opts in data)):
        minutes = sum((data[k][1][j][1] for k, j in enumerate(idx)), Fraction(0))
        if minutes > budget:
            continue
        feasible += 1
        mismatch = sum((abs(data[k][1][j][0] - data[k][0]) for k, j in enumerate(idx)), Fraction(0))
        if best is None or (mismatch, minutes) < (best[0], best[1]):
            best = (mismatch, minutes, idx)
    if best is None:
        raise ValueError('no encounter selection fits the minutes budget')
    mismatch, minutes, idx = best
    return {'option_indices': list(idx), 'total_mismatch': mismatch, 'total_minutes': minutes,
            'beat_mismatches': [abs(data[k][1][j][0] - data[k][0]) for k, j in enumerate(idx)],
            'feasible_count': feasible, 'aligned': mismatch == 0,
            'story_quality_validated': False, 'not_claimed': NOT_CLAIMED}
