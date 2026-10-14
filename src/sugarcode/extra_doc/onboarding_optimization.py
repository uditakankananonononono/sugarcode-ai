"""Row 446, Onboarding Optimization (PARTIAL: one exact step-drop rule): check a supplied onboarding-step list.

check_steps(steps) takes steps as a list of 0 to 40 tuples (step, completions, minutes): step 1 to 24 lowercase
identifier characters, completions an exact integer 0 to 100000, minutes an exact integer 0 to 1440 (median time
to complete). The rules, applied to each step i (0-based) in supplied order, are:
  completions exceed the immediately previous step's, else (i, 'drop_inverted');
  completions below half the immediately previous step's when that step is nonzero, else (i, 'drop_steep');
  minutes over 30, else (i, 'slow_step').
The first step cannot raise drop_inverted or drop_steep. It returns {'problems': sorted (index, code), 'steps': sorted distinct steps
present, 'total': the step count}.
Order of checks: steps (list type, count, then each in order: tuple type, 3 items, step type and shape,
completions type and range, minutes type and range), and only then the rules.

NOT_CLAIMED: this checks a supplied step list against two drop bars and one time bar. It does not say the
first experience improves, that half or 30 minutes are the right bars, or that any user finished onboarding. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_steps(steps):
    if type(steps) is not list:
        raise TypeError('steps must be an exact list')
    if len(steps) > 40:
        raise ValueError('step count must be at most 40')
    for s in steps:
        if type(s) is not tuple:
            raise TypeError('each step must be an exact tuple')
        if len(s) != 3:
            raise ValueError('each step must have 3 items')
        if type(s[0]) is not str:
            raise TypeError('step must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('step must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not int:
            raise TypeError('completions must be an exact integer')
        if not 0 <= s[1] <= 100000:
            raise ValueError('completions must be 0 to 100000')
        if type(s[2]) is not int:
            raise TypeError('minutes must be an exact integer')
        if not 0 <= s[2] <= 1440:
            raise ValueError('minutes must be 0 to 1440')
    problems = []
    names = set()
    previous = None
    for i, (step, completions, minutes) in enumerate(steps):
        if previous is not None:
            if completions > previous:
                problems.append((i, 'drop_inverted'))
            elif previous and completions * 2 < previous:
                problems.append((i, 'drop_steep'))
        if minutes > 30:
            problems.append((i, 'slow_step'))
        names.add(step)
        previous = completions
    return {'problems': sorted(problems), 'steps': sorted(names), 'total': len(steps)}
