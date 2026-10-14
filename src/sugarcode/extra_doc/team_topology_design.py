"""Row 481, Team Topology Design (PARTIAL: one exact team check): each team is an
exact tuple (team, size, dependencies) - team an exact string of 1 to 24 lowercase
identifier characters, size an exact integer 0 to 20 of members, dependencies an exact
integer 0 to 10 of other teams it must wait on. A team is checked against two flow
bars, and each bar it fails adds (index, code) to problems:
  size over 9, else (i, 'oversized');
  dependencies over 2, else (i, 'tangled').
Checks run in this order: teams must be an exact list; team count must be at most 40;
each team must be an exact tuple; each team must have 3 items; team must be an exact
string; team must be 1 to 24 lowercase identifier characters; size must be an exact
integer; size must be 0 to 20; dependencies must be an exact integer; dependencies
must be 0 to 10. Returns {'problems': sorted, 'teams': sorted distinct, 'total':
number of teams}.

NOT_CLAIMED: this checks supplied team numbers against two flow bars. It does not say
the structure flows, that 9 members or 2 dependencies are the right bars, or that any
team ships. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_flow(teams):
    """Flag teams outside the flow bars."""
    if type(teams) is not list:
        raise TypeError('teams must be an exact list')
    if len(teams) > 40:
        fail('team count must be at most 40')
    problems = []
    names = set()
    for i, team in enumerate(teams):
        if type(team) is not tuple:
            raise TypeError('each team must be an exact tuple')
        if len(team) != 3:
            fail('each team must have 3 items')
        name, size, dependencies = team
        if type(name) is not str:
            raise TypeError('team must be an exact string')
        if not LABEL.match(name):
            fail('team must be 1 to 24 lowercase identifier characters')
        if type(size) is not int:
            raise TypeError('size must be an exact integer')
        if not 0 <= size <= 20:
            fail('size must be 0 to 20')
        if type(dependencies) is not int:
            raise TypeError('dependencies must be an exact integer')
        if not 0 <= dependencies <= 10:
            fail('dependencies must be 0 to 10')
        if size > 9:
            problems.append((i, 'oversized'))
        if dependencies > 2:
            problems.append((i, 'tangled'))
        names.add(name)
    return {'problems': sorted(problems), 'teams': sorted(names), 'total': len(teams)}
