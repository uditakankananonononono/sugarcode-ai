"""Row 560, Question Answering (PARTIAL: one exact system check): each system is an
exact tuple (system, coverage, latency_ms) - system an exact string of 1 to 24
lowercase identifier characters, coverage an exact integer 0 to 100 percent of
evaluation questions answered, latency_ms an exact integer 0 to 10000. A system is
checked against two answer bars, and each bar it fails adds (index, code) to problems:
  coverage below 80, else (i, 'low_coverage');
  latency_ms over 500, else (i, 'slow_answer').
Checks run in this order: systems must be an exact list; system count must be at most
40; each system must be an exact tuple; each system must have 3 items; system must be
an exact string; system must be 1 to 24 lowercase identifier characters; coverage must
be an exact integer; coverage must be 0 to 100; latency_ms must be an exact integer;
latency_ms must be 0 to 10000. Returns {'problems': sorted, 'systems': sorted
distinct, 'total': number of systems}.

NOT_CLAIMED: this checks supplied evaluation numbers against two answer bars. It does
not say queries are answered, that 80 percent or 500 ms are the right bars, or that
any answer is right. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_systems(systems):
    """Flag systems outside the answer bars."""
    if type(systems) is not list:
        raise TypeError('systems must be an exact list')
    if len(systems) > 40:
        fail('system count must be at most 40')
    problems = []
    names = set()
    for i, system in enumerate(systems):
        if type(system) is not tuple:
            raise TypeError('each system must be an exact tuple')
        if len(system) != 3:
            fail('each system must have 3 items')
        name, coverage, latency_ms = system
        if type(name) is not str:
            raise TypeError('system must be an exact string')
        if not LABEL.match(name):
            fail('system must be 1 to 24 lowercase identifier characters')
        if type(coverage) is not int:
            raise TypeError('coverage must be an exact integer')
        if not 0 <= coverage <= 100:
            fail('coverage must be 0 to 100')
        if type(latency_ms) is not int:
            raise TypeError('latency_ms must be an exact integer')
        if not 0 <= latency_ms <= 10000:
            fail('latency_ms must be 0 to 10000')
        if coverage < 80:
            problems.append((i, 'low_coverage'))
        if latency_ms > 500:
            problems.append((i, 'slow_answer'))
        names.add(name)
    return {'problems': sorted(problems), 'systems': sorted(names), 'total': len(systems)}
