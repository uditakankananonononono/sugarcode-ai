"""Row 477, Training Design (PARTIAL: one exact program check): each program is an
exact tuple (module, hours, pass_rate) - module an exact string of 1 to 24 lowercase
identifier characters, hours an exact integer 0 to 40 of delivered training, pass_rate
an exact integer 0 to 100. A program is checked against two delivery bars, and each
bar it fails adds (index, code) to problems:
  hours below 2, else (i, 'too_brief');
  pass_rate below 70, else (i, 'low_pass').
Checks run in this order: programs must be an exact list; program count must be at
most 40; each program must be an exact tuple; each program must have 3 items; module
must be an exact string; module must be 1 to 24 lowercase identifier characters;
hours must be an exact integer; hours must be 0 to 40; pass_rate must be an exact
integer; pass_rate must be 0 to 100. Returns {'problems': sorted, 'modules': sorted
distinct, 'total': number of programs}.

NOT_CLAIMED: this checks supplied program numbers against two delivery bars. It does
not say capabilities develop, that 2 hours or 70 are the right bars, or that anyone
learned. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_programs(programs):
    """Flag programs under the brief or pass bars."""
    if type(programs) is not list:
        raise TypeError('programs must be an exact list')
    if len(programs) > 40:
        fail('program count must be at most 40')
    problems = []
    names = set()
    for i, program in enumerate(programs):
        if type(program) is not tuple:
            raise TypeError('each program must be an exact tuple')
        if len(program) != 3:
            fail('each program must have 3 items')
        module, hours, pass_rate = program
        if type(module) is not str:
            raise TypeError('module must be an exact string')
        if not LABEL.match(module):
            fail('module must be 1 to 24 lowercase identifier characters')
        if type(hours) is not int:
            raise TypeError('hours must be an exact integer')
        if not 0 <= hours <= 40:
            fail('hours must be 0 to 40')
        if type(pass_rate) is not int:
            raise TypeError('pass_rate must be an exact integer')
        if not 0 <= pass_rate <= 100:
            fail('pass_rate must be 0 to 100')
        if hours < 2:
            problems.append((i, 'too_brief'))
        if pass_rate < 70:
            problems.append((i, 'low_pass'))
        names.add(module)
    return {'problems': sorted(problems), 'modules': sorted(names), 'total': len(programs)}
