"""Row 691, Pair Programming (PARTIAL: one exact rotation rule): check a driver and navigator schedule.

check_pairing(turns) takes turns as a list of (start, end, driver, navigator): minutes from the start of the session (exact ints)
and two names. The rules, applied to each turn i (0-based), are:
  the first turn starts at minute 0, else (0, 'late_start');
  end > start, else (i, 'empty_turn');
  end - start <= 30, else (i, 'too_long');
  driver != navigator, else (i, 'same_person');
  for i > 0: start == the previous end, else (i, 'gap_or_overlap'); and driver == the previous navigator, else (i, 'no_swap').
One turn can break several rules; all are reported. It returns {'problems': sorted (index, code), 'driving': {name: minutes}
for every driver, counting end - start of each turn whose end is above its start, 'total': the end of the last turn or 0}.
Caps: 0 to 40 turns, minutes 0 to 600, names 1 to 24 lowercase identifier characters.
Order of checks: turns (list type, count, then each in order: tuple type, 4 items, start type and range, end type and range,
driver name type and shape, navigator name type and shape), and only then the rules.

NOT_CLAIMED: this checks a supplied schedule. It does not say that pairing helped, that the two people worked well together, or
that the turn lengths suit them. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def _minute(v):
    if type(v) is not int:
        raise TypeError('minute must be an exact int')
    if not 0 <= v <= 600:
        raise ValueError('minute must be between 0 and 600')


def _name(v):
    if type(v) is not str:
        raise TypeError('name must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError('name must be 1 to 24 lowercase identifier characters')


def check_pairing(turns):
    if type(turns) is not list:
        raise TypeError('turns must be an exact list')
    if len(turns) > 40:
        raise ValueError('turn count must be at most 40')
    for t in turns:
        if type(t) is not tuple:
            raise TypeError('each turn must be an exact tuple')
        if len(t) != 4:
            raise ValueError('each turn must have 4 items')
        _minute(t[0])
        _minute(t[1])
        _name(t[2])
        _name(t[3])
    problems = []
    driving = {}
    prev = None
    for i, (start, end, driver, navigator) in enumerate(turns):
        if prev is None:
            if start != 0:
                problems.append((i, 'late_start'))
        else:
            if start != prev[1]:
                problems.append((i, 'gap_or_overlap'))
            if driver != prev[3]:
                problems.append((i, 'no_swap'))
        if end <= start:
            problems.append((i, 'empty_turn'))
        else:
            driving[driver] = driving.get(driver, 0) + end - start
            if end - start > 30:
                problems.append((i, 'too_long'))
        if driver == navigator:
            problems.append((i, 'same_person'))
        prev = (start, end, driver, navigator)
    return {'problems': sorted(problems), 'driving': dict(sorted(driving.items())),
            'total': turns[-1][1] if turns else 0}
