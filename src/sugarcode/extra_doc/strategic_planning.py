"""Row 490, Strategic Planning (PARTIAL: one exact plan check): each plan is an exact
tuple (plan, goals, milestones) - plan an exact string of 1 to 24 lowercase identifier
characters, goals an exact integer 0 to 15 of named goals, milestones an exact integer
0 to 30 of dated milestones. A plan is checked against two direction bars, and each
bar it fails adds (index, code) to problems:
  goals below 1, else (i, 'adrift');
  milestones below 2, else (i, 'sparse').
Checks run in this order: plans must be an exact list; plan count must be at most 40;
each plan must be an exact tuple; each plan must have 3 items; plan must be an exact
string; plan must be 1 to 24 lowercase identifier characters; goals must be an exact
integer; goals must be 0 to 15; milestones must be an exact integer; milestones must
be 0 to 30. Returns {'problems': sorted, 'plans': sorted distinct, 'total': number of
plans}.

NOT_CLAIMED: this checks supplied plan numbers against two direction bars. It does not
say a direction is set, that 1 goal or 2 milestones are the right bars, or that any
goal is reached. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_plans(plans):
    """Flag plans outside the direction bars."""
    if type(plans) is not list:
        raise TypeError('plans must be an exact list')
    if len(plans) > 40:
        fail('plan count must be at most 40')
    problems = []
    names = set()
    for i, plan in enumerate(plans):
        if type(plan) is not tuple:
            raise TypeError('each plan must be an exact tuple')
        if len(plan) != 3:
            fail('each plan must have 3 items')
        name, goals, milestones = plan
        if type(name) is not str:
            raise TypeError('plan must be an exact string')
        if not LABEL.match(name):
            fail('plan must be 1 to 24 lowercase identifier characters')
        if type(goals) is not int:
            raise TypeError('goals must be an exact integer')
        if not 0 <= goals <= 15:
            fail('goals must be 0 to 15')
        if type(milestones) is not int:
            raise TypeError('milestones must be an exact integer')
        if not 0 <= milestones <= 30:
            fail('milestones must be 0 to 30')
        if goals < 1:
            problems.append((i, 'adrift'))
        if milestones < 2:
            problems.append((i, 'sparse'))
        names.add(name)
    return {'problems': sorted(problems), 'plans': sorted(names), 'total': len(plans)}
