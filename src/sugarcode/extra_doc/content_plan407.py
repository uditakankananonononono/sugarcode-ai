"""Row 407, Content Strategy: choosing which supplied topics fit a content budget.

Plans content creation by ranking. topics is a list or tuple of 1 to 30
(name, priority, effort) rows, each a 3-tuple or 3-list. name is a str of
1 to 40 characters and must differ from every other name (compared
exactly); priority and effort are nonbool ints from 1 to 5. capacity is a
nonbool int from 0 to 100, the effort the plan may spend. Topics are ranked
by priority high to low, then effort low to high, then supplied order.
Walking that ranking, a topic is planned when its effort still fits in the
remaining capacity, else skipped; the walk continues past a skipped topic.
Reported: planned (names in ranking order), skipped (names in ranking
order) and spent (total effort planned). Checks, in this order: capacity,
topics type, topics size, then each row in order: row shape, name,
priority, effort, duplicate name.
NOT_CLAIMED: audience research, content quality, channel choice, real
effort estimation, production readiness.
"""
SCOPE = 'PARTIAL: priority and effort ranking against a supplied budget, no real strategy'
NOT_CLAIMED = ('audience research', 'content quality', 'channel choice',
               'real effort estimation', 'production readiness')

MAX_TOPICS = 30
MAX_NAME = 40
MAX_CAPACITY = 100
MAX_SCORE = 5


def plan(topics, capacity):
    if type(capacity) is not int or not 0 <= capacity <= MAX_CAPACITY:
        raise ValueError('capacity must be a nonbool int from 0 to 100')
    if type(topics) not in (list, tuple):
        raise TypeError('topics must be a list or tuple')
    if not 1 <= len(topics) <= MAX_TOPICS:
        raise ValueError('topics must hold 1 to 30 rows')
    seen = set()
    for row in topics:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each topic must be a (name, priority, effort) list or tuple')
        name, priority, effort = row
        if type(name) is not str or not 1 <= len(name) <= MAX_NAME:
            raise ValueError('names must be str of 1 to 40 characters')
        if type(priority) is not int or not 1 <= priority <= MAX_SCORE:
            raise ValueError('priority must be a nonbool int from 1 to 5')
        if type(effort) is not int or not 1 <= effort <= MAX_SCORE:
            raise ValueError('effort must be a nonbool int from 1 to 5')
        if name in seen:
            raise ValueError('names must be distinct')
        seen.add(name)
    order = sorted(range(len(topics)), key=lambda i: (-topics[i][1], topics[i][2], i))
    planned, skipped, left = [], [], capacity
    for i in order:
        name, _, effort = topics[i]
        if effort <= left:
            planned.append(name)
            left -= effort
        else:
            skipped.append(name)
    return {'planned': planned, 'skipped': skipped, 'spent': capacity - left}
