"""Row 479, Span of Control (PARTIAL: one exact team check): each team is an exact
tuple (manager, reports) - manager an exact string of 1 to 24 lowercase identifier
characters, reports an exact integer 0 to 100 of direct reports. A team is checked
against two ratio bars, and each bar it fails adds (index, code) to problems:
  reports over 10, else (i, 'overloaded');
  reports below 3, else (i, 'narrow').
Checks run in this order: teams must be an exact list; team count must be at most 40;
each team must be an exact tuple; each team must have 2 items; manager must be an
exact string; manager must be 1 to 24 lowercase identifier characters; reports must
be an exact integer; reports must be 0 to 100. Returns {'problems': sorted,
'managers': sorted distinct, 'total': number of teams}.

NOT_CLAIMED: this checks supplied report counts against two ratio bars. It does not
say the management ratio is right, that 3 or 10 are the right bars, or that any team
is well run. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_teams(teams):
    """Flag teams outside the span bars."""
    if type(teams) is not list:
        raise TypeError('teams must be an exact list')
    if len(teams) > 40:
        fail('team count must be at most 40')
    problems = []
    names = set()
    for i, team in enumerate(teams):
        if type(team) is not tuple:
            raise TypeError('each team must be an exact tuple')
        if len(team) != 2:
            fail('each team must have 2 items')
        manager, reports = team
        if type(manager) is not str:
            raise TypeError('manager must be an exact string')
        if not LABEL.match(manager):
            fail('manager must be 1 to 24 lowercase identifier characters')
        if type(reports) is not int:
            raise TypeError('reports must be an exact integer')
        if not 0 <= reports <= 100:
            fail('reports must be 0 to 100')
        if reports > 10:
            problems.append((i, 'overloaded'))
        if reports < 3:
            problems.append((i, 'narrow'))
        names.add(manager)
    return {'problems': sorted(problems), 'managers': sorted(names), 'total': len(teams)}
