"""Row 687, Test-Driven Development (PARTIAL: one exact cycle rule): check a red, green, refactor log against the TDD cycle.

check_cycle(log) takes log as a list of (phase, passed, failed): phase is 'red', 'green' or 'refactor' and passed and failed
are the test counts after that step, exact ints from 0 to 1000. Rules, per entry i:
  order     the first entry must be red; after red only green; after green only refactor or red; after refactor only refactor
            or red (green never follows refactor), else (i, 'bad_order');
  red       needs failed >= 1, else (i, 'red_without_failure');
  green     needs failed == 0, else (i, 'green_with_failure');
  refactor  needs failed == 0, else (i, 'refactor_with_failure'); and passed >= the passed of the entry before it, else
            (i, 'refactor_lost_tests').
One entry can break several rules; all are reported. It returns {'problems': sorted (index, code), 'cycles': the number of
entries that are a green straight after a red, 'last_phase': the phase of the last entry or None}.
Caps: 0 to 60 entries.
Order of checks: log (list type, count, then each in order: tuple type, 3 items, phase type and value, passed type and range,
failed type and range), and only then the rules.

NOT_CLAIMED: this checks counts and phase order in a supplied log. It does not run tests, say that a test is a good test, or
say that a team really worked test first. No clinical or wet-lab claim.
"""
PHASES = ('red', 'green', 'refactor')
AFTER = {None: ('red',), 'red': ('green',), 'green': ('refactor', 'red'), 'refactor': ('refactor', 'red')}


def _count(v):
    if type(v) is not int:
        raise TypeError('count must be an exact int')
    if not 0 <= v <= 1000:
        raise ValueError('count must be between 0 and 1000')


def check_cycle(log):
    if type(log) is not list:
        raise TypeError('log must be an exact list')
    if len(log) > 60:
        raise ValueError('entry count must be at most 60')
    for e in log:
        if type(e) is not tuple:
            raise TypeError('each entry must be an exact tuple')
        if len(e) != 3:
            raise ValueError('each entry must have 3 items')
        if type(e[0]) is not str:
            raise TypeError('phase must be an exact string')
        if e[0] not in PHASES:
            raise ValueError("phase must be 'red', 'green' or 'refactor'")
        _count(e[1])
        _count(e[2])
    problems = []
    cycles = 0
    prev = None
    prev_passed = None
    for i, (phase, passed, failed) in enumerate(log):
        if phase not in AFTER[prev]:
            problems.append((i, 'bad_order'))
        if phase == 'red' and failed < 1:
            problems.append((i, 'red_without_failure'))
        if phase == 'green':
            cycles += prev == 'red'
            if failed != 0:
                problems.append((i, 'green_with_failure'))
        if phase == 'refactor':
            if failed != 0:
                problems.append((i, 'refactor_with_failure'))
            if prev_passed is not None and passed < prev_passed:
                problems.append((i, 'refactor_lost_tests'))
        prev = phase
        prev_passed = passed
    return {'problems': sorted(problems), 'cycles': cycles, 'last_phase': prev}
