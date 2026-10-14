"""Row 487, SWOT Analysis (PARTIAL: one exact subject check): each subject is an exact
tuple (subject, positives, negatives) - subject an exact string of 1 to 24 lowercase
identifier characters, positives an exact integer 0 to 20 of strengths and
opportunities listed, negatives an exact integer 0 to 20 of weaknesses and threats
listed. A subject is checked against two position bars, and each bar it fails adds
(index, code) to problems:
  positives below 1 or negatives below 1, else (i, 'one_sided');
  positives and negatives together below 4, else (i, 'shallow').
Checks run in this order: subjects must be an exact list; subject count must be at
most 40; each subject must be an exact tuple; each subject must have 3 items; subject
must be an exact string; subject must be 1 to 24 lowercase identifier characters;
positives must be an exact integer; positives must be 0 to 20; negatives must be an
exact integer; negatives must be 0 to 20. Returns {'problems': sorted, 'subjects':
sorted distinct, 'total': number of subjects}.

NOT_CLAIMED: this checks supplied factor counts against two position bars. It does not
say the position is assessed, that 1 factor a side or 4 in total are the right bars,
or that any factor is real. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_subjects(subjects):
    """Flag subjects outside the position bars."""
    if type(subjects) is not list:
        raise TypeError('subjects must be an exact list')
    if len(subjects) > 40:
        fail('subject count must be at most 40')
    problems = []
    names = set()
    for i, subject in enumerate(subjects):
        if type(subject) is not tuple:
            raise TypeError('each subject must be an exact tuple')
        if len(subject) != 3:
            fail('each subject must have 3 items')
        name, positives, negatives = subject
        if type(name) is not str:
            raise TypeError('subject must be an exact string')
        if not LABEL.match(name):
            fail('subject must be 1 to 24 lowercase identifier characters')
        if type(positives) is not int:
            raise TypeError('positives must be an exact integer')
        if not 0 <= positives <= 20:
            fail('positives must be 0 to 20')
        if type(negatives) is not int:
            raise TypeError('negatives must be an exact integer')
        if not 0 <= negatives <= 20:
            fail('negatives must be 0 to 20')
        if positives < 1 or negatives < 1:
            problems.append((i, 'one_sided'))
        if positives + negatives < 4:
            problems.append((i, 'shallow'))
        names.add(name)
    return {'problems': sorted(problems), 'subjects': sorted(names), 'total': len(subjects)}
