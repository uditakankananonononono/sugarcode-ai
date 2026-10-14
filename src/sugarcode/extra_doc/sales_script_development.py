"""Row 430, Sales Script Development (PARTIAL: one exact phase-order rule): check a supplied script-beat list.

check_beats(beats) takes beats as a list of 0 to 40 tuples (beat, phase): beat 1 to 24 lowercase identifier
characters, phase an exact string 'opening', 'discovery', 'pitch' or 'close'. Phases rank opening 0, discovery 1,
pitch 2, close 3; furthest is the highest rank of all earlier beats (none yet: -1). The rules, applied to each
beat i (0-based) in supplied order, are:
  its phase ranks below furthest, else (i, 'phase_back');
  its phase ranks more than one above furthest, else (i, 'phase_skip').
It returns {'problems': sorted (index, code), 'beats': sorted distinct beats present, 'total': the beat count}.
Order of checks: beats (list type, count, then each in order: tuple type, 2 items, beat type and shape, phase
type and membership), and only then the rules.

NOT_CLAIMED: this checks a supplied beat list against one phase-order rule. It does not say the script structures
a good pitch, that the four phases are the right model, or that any pitch was delivered. No clinical or wet-lab
claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
PHASES = ('opening', 'discovery', 'pitch', 'close')


def check_beats(beats):
    if type(beats) is not list:
        raise TypeError('beats must be an exact list')
    if len(beats) > 40:
        raise ValueError('beat count must be at most 40')
    for s in beats:
        if type(s) is not tuple:
            raise TypeError('each beat must be an exact tuple')
        if len(s) != 2:
            raise ValueError('each beat must have 2 items')
        if type(s[0]) is not str:
            raise TypeError('beat must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('beat must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not str:
            raise TypeError('phase must be an exact string')
        if s[1] not in PHASES:
            raise ValueError('phase must be opening, discovery, pitch or close')
    problems = []
    names = set()
    furthest = -1
    for i, (beat, phase) in enumerate(beats):
        rank = PHASES.index(phase)
        if rank < furthest:
            problems.append((i, 'phase_back'))
        elif rank > furthest + 1:
            problems.append((i, 'phase_skip'))
        furthest = max(furthest, rank)
        names.add(beat)
    return {'problems': sorted(problems), 'beats': sorted(names), 'total': len(beats)}
