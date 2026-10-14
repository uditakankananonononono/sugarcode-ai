"""Row 480, Matrix Organization (PARTIAL: one exact member check): each member is an
exact tuple (person, managers, projects) - person an exact string of 1 to 24 lowercase
identifier characters, managers an exact integer 0 to 5 of reporting lines, projects
an exact integer 0 to 10. A member is checked against two balance bars, and each bar
it fails adds (index, code) to problems:
  managers below 2, else (i, 'unmatrixed');
  projects over 3, else (i, 'overloaded').
Checks run in this order: members must be an exact list; member count must be at most
40; each member must be an exact tuple; each member must have 3 items; person must be
an exact string; person must be 1 to 24 lowercase identifier characters; managers must
be an exact integer; managers must be 0 to 5; projects must be an exact integer;
projects must be 0 to 10. Returns {'problems': sorted, 'members': sorted distinct,
'total': number of members}.

NOT_CLAIMED: this checks supplied matrix numbers against two balance bars. It does not
say functions balance, that 2 managers or 3 projects are the right bars, or that any
member works well. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_members(members):
    """Flag members outside the matrix bars."""
    if type(members) is not list:
        raise TypeError('members must be an exact list')
    if len(members) > 40:
        fail('member count must be at most 40')
    problems = []
    names = set()
    for i, member in enumerate(members):
        if type(member) is not tuple:
            raise TypeError('each member must be an exact tuple')
        if len(member) != 3:
            fail('each member must have 3 items')
        person, managers, projects = member
        if type(person) is not str:
            raise TypeError('person must be an exact string')
        if not LABEL.match(person):
            fail('person must be 1 to 24 lowercase identifier characters')
        if type(managers) is not int:
            raise TypeError('managers must be an exact integer')
        if not 0 <= managers <= 5:
            fail('managers must be 0 to 5')
        if type(projects) is not int:
            raise TypeError('projects must be an exact integer')
        if not 0 <= projects <= 10:
            fail('projects must be 0 to 10')
        if managers < 2:
            problems.append((i, 'unmatrixed'))
        if projects > 3:
            problems.append((i, 'overloaded'))
        names.add(person)
    return {'problems': sorted(problems), 'members': sorted(names), 'total': len(members)}
