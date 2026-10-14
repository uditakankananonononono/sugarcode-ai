"""Row 871, Paradigm Shifting (PARTIAL: one exact assumption rule).

Each supplied model is checked with two assumption bars:
- 'entrenched' when challenges < 1
- 'overloaded' when anomalies > 5

NOT_CLAIMED: this checks supplied model numbers against two assumption bars. It does not say any paradigm shifts, that 1 challenge or 5 anomalies are the right bars, or that any model is replaced. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_models(models):
    if type(models) is not list:
        raise TypeError('models must be an exact list')
    if len(models) > 40:
        raise ValueError('model count must be at most 40')
    problems = []
    for i, item in enumerate(models):
        if type(item) is not tuple:
            raise TypeError('each model must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each model must have 3 items')
        name, challenges, anomalies = item
        if type(name) is not str:
            raise TypeError('model must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('model must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('challenges', challenges, 20), ('anomalies', anomalies, 50)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if challenges < 1:
            problems.append((i, 'entrenched'))
        if anomalies > 5:
            problems.append((i, 'overloaded'))
    return {'problems': sorted(problems),
            'models': sorted({x[0] for x in models}),
            'total': len(models)}
