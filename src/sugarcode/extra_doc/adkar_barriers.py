"""Row 475 ADKAR Model: exact barrier-point table from caller-scored individuals.

The caller supplies 1 to 20 people (label, scores) and a barrier threshold (int 1 to 5). scores
is five ints from 1 to 5 in the model's order Awareness, Desire, Knowledge, Ability,
Reinforcement. A person's barrier point is the first element in that order scoring at or below
the threshold (None when none does). Reported: per person the barrier point, per element the
mean score (Fraction) and how many people have it as their barrier point, and the most common
barrier point (first in model order on ties, None when nobody has one). Labels are caller
strings, not identities. Caps are implementation choices, not spec values. Nothing is surveyed.
Element names checked against https://www.prosci.com/methodology/adkar on 2026-10-14.
NOT_CLAIMED: that the scores are measured or meaningful, that the order of elements is how a
person actually changes, anything about any real individual, that acting on a barrier works,
employment, consultation or privacy obligations, approval-gate clearance, deployment.
"""
from fractions import Fraction

ELEMENTS = ('Awareness', 'Desire', 'Knowledge', 'Ability', 'Reinforcement')
NOT_CLAIMED = ('scores measured or meaningful', 'the order of elements is how a person changes',
               'anything about any real individual', 'acting on a barrier works',
               'employment, consultation or privacy obligations', 'approval-gate clearance', 'deployment')


def adkar_barriers(people, threshold):
    if type(threshold) is not int:
        raise TypeError('threshold must be nonbool int')
    if not 1 <= threshold <= 5:
        raise ValueError('threshold must be between 1 and 5')
    if type(people) not in (list, tuple):
        raise TypeError('people must be a list or tuple')
    if not 1 <= len(people) <= 20:
        raise ValueError('people count must be between 1 and 20')
    rows = []
    for p in people:
        if type(p) not in (list, tuple) or len(p) != 2:
            raise ValueError('each person must be (label, scores)')
        label, scores = p
        if type(label) is not str:
            raise TypeError('labels must be str')
        if not 1 <= len(label) <= 40:
            raise ValueError('labels must be 1 to 40 characters')
        if type(scores) not in (list, tuple) or len(scores) != 5:
            raise ValueError('scores must hold 5 entries')
        for s in scores:
            if type(s) is not int:
                raise TypeError('scores must be nonbool int')
            if not 1 <= s <= 5:
                raise ValueError('scores must be between 1 and 5')
        rows.append((label, tuple(scores)))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('labels must be unique')
    barrier = [next((j for j, s in enumerate(sc) if s <= threshold), None) for _, sc in rows]
    per = [{'label': l, 'barrier': ELEMENTS[b] if b is not None else None} for (l, _), b in zip(rows, barrier)]
    elems = [{'element': e, 'mean': Fraction(sum(r[1][j] for r in rows), len(rows)),
              'barrier_count': barrier.count(j)} for j, e in enumerate(ELEMENTS)]
    top = max(range(5), key=lambda j: (elems[j]['barrier_count'], -j))
    return {'people': per, 'elements': elems,
            'most_common_barrier': ELEMENTS[top] if elems[top]['barrier_count'] else None,
            'adkar_validated': False, 'not_claimed': NOT_CLAIMED}
