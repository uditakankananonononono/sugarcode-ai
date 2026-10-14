"""Row 492, KPI Selection (PARTIAL: one exact metric check): each metric is an exact
tuple (metric, sources, reviews) - metric an exact string of 1 to 24 lowercase
identifier characters, sources an exact integer 0 to 10 of data sources feeding it,
reviews an exact integer 0 to 12 of scheduled reviews. A metric is checked against two
choice bars, and each bar it fails adds (index, code) to problems:
  sources below 1, else (i, 'unsourced');
  reviews below 2, else (i, 'drifting').
Checks run in this order: metrics must be an exact list; metric count must be at most
40; each metric must be an exact tuple; each metric must have 3 items; metric must be
an exact string; metric must be 1 to 24 lowercase identifier characters; sources must
be an exact integer; sources must be 0 to 10; reviews must be an exact integer;
reviews must be 0 to 12. Returns {'problems': sorted, 'metrics': sorted distinct,
'total': number of metrics}.

NOT_CLAIMED: this checks supplied metric numbers against two choice bars. It does not
say the right metrics were chosen, that 1 source or 2 reviews are the right bars, or
that any number moves. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_metrics(metrics):
    """Flag metrics outside the choice bars."""
    if type(metrics) is not list:
        raise TypeError('metrics must be an exact list')
    if len(metrics) > 40:
        fail('metric count must be at most 40')
    problems = []
    names = set()
    for i, metric in enumerate(metrics):
        if type(metric) is not tuple:
            raise TypeError('each metric must be an exact tuple')
        if len(metric) != 3:
            fail('each metric must have 3 items')
        name, sources, reviews = metric
        if type(name) is not str:
            raise TypeError('metric must be an exact string')
        if not LABEL.match(name):
            fail('metric must be 1 to 24 lowercase identifier characters')
        if type(sources) is not int:
            raise TypeError('sources must be an exact integer')
        if not 0 <= sources <= 10:
            fail('sources must be 0 to 10')
        if type(reviews) is not int:
            raise TypeError('reviews must be an exact integer')
        if not 0 <= reviews <= 12:
            fail('reviews must be 0 to 12')
        if sources < 1:
            problems.append((i, 'unsourced'))
        if reviews < 2:
            problems.append((i, 'drifting'))
        names.add(name)
    return {'problems': sorted(problems), 'metrics': sorted(names), 'total': len(metrics)}
