"""Row 791, Curiosity (PARTIAL: one exact inquiry rule).

Each supplied topic is checked with two inquiry bars:
- 'incurious' when questions < 3
- 'shallow' when follow_ups < 1

NOT_CLAIMED: this checks supplied topic numbers against two inquiry bars. It does not say anyone is curious, that 3 questions or 1 follow-up are the right bars, or that anything is discovered. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_topics(topics):
    if type(topics) is not list:
        raise TypeError('topics must be an exact list')
    if len(topics) > 40:
        raise ValueError('topic count must be at most 40')
    problems = []
    for i, item in enumerate(topics):
        if type(item) is not tuple:
            raise TypeError('each topic must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each topic must have 3 items')
        name, questions, follow_ups = item
        if type(name) is not str:
            raise TypeError('topic must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('topic must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('questions', questions, 100), ('follow_ups', follow_ups, 50)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if questions < 3:
            problems.append((i, 'incurious'))
        if follow_ups < 1:
            problems.append((i, 'shallow'))
    return {'problems': sorted(problems),
            'topics': sorted({x[0] for x in topics}),
            'total': len(topics)}
