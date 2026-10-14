"""Row 486, Strategy Development (PARTIAL: one exact plan check): each plan is an
exact tuple (plan, moves, reviews) - plan an exact string of 1 to 24 lowercase
identifier characters, moves an exact integer 0 to 20 of competitive moves planned,
reviews an exact integer 0 to 12 of scheduled reviews. A plan is checked against two
approach bars, and each bar it fails adds (index, code) to problems:
  moves below 1, else (i, 'inert');
  reviews below 2, else (i, 'unchecked').
Checks run in this order: plans must be an exact list; plan count must be at most 40;
each plan must be an exact tuple; each plan must have 3 items; plan must be an exact
string; plan must be 1 to 24 lowercase identifier characters; moves must be an exact
integer; moves must be 0 to 20; reviews must be an exact integer; reviews must be 0 to
12. Returns {'problems': sorted, 'plans': sorted distinct, 'total': number of plans}.

NOT_CLAIMED: this checks supplied plan numbers against two approach bars. It does not
say the approach competes, that 1 move or 2 reviews are the right bars, or that any
plan wins. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_plans(plans):
    """Flag plans outside the approach bars."""
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
        name, moves, reviews = plan
        if type(name) is not str:
            raise TypeError('plan must be an exact string')
        if not LABEL.match(name):
            fail('plan must be 1 to 24 lowercase identifier characters')
        if type(moves) is not int:
            raise TypeError('moves must be an exact integer')
        if not 0 <= moves <= 20:
            fail('moves must be 0 to 20')
        if type(reviews) is not int:
            raise TypeError('reviews must be an exact integer')
        if not 0 <= reviews <= 12:
            fail('reviews must be 0 to 12')
        if moves < 1:
            problems.append((i, 'inert'))
        if reviews < 2:
            problems.append((i, 'unchecked'))
        names.add(name)
    return {'problems': sorted(problems), 'plans': sorted(names), 'total': len(plans)}
