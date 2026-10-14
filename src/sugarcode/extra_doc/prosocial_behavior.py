"""Row 767, Prosocial Behavior: totaling supplied beneficial acts.

Benefits others by counting. Each row pairs an actor name of 1 to 8
characters with the number of people helped, an integer from 1 to
10. Reported: the act count, the total people helped, how many
distinct actors appear, and the actor who helped the most people in
total (ties broken alphabetically, None when there are no acts).
Caps (checked before any work): 0 to 100 rows.
NOT_CLAIMED: real behavior, social psychology, volunteering,
community outcomes, motivation, measurement, production readiness.
"""
SCOPE = 'PARTIAL: benefit totaling over supplied rows, no real prosocial behavior'
NOT_CLAIMED = ('real behavior', 'social psychology', 'volunteering',
               'community outcomes', 'motivation', 'measurement',
               'production readiness')

MAX_ROWS = 100
MAX_ACTOR = 8
MAX_PEOPLE = 10


def benefit(acts):
    if type(acts) not in (list, tuple):
        raise TypeError('acts must be a list or tuple')
    if len(acts) > MAX_ROWS:
        raise ValueError('acts must contain at most 100 rows')
    rows = []
    for row in acts:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each act must be an (actor, people) row')
        actor, people = row
        if type(actor) is not str or not 1 <= len(actor) <= MAX_ACTOR:
            raise ValueError('actor must be a string of 1 to 8 characters')
        if type(people) is not int or not 1 <= people <= MAX_PEOPLE:
            raise ValueError('people must be an integer from 1 to 10')
        rows.append((actor, people))
    totals = {}
    helped = 0
    for actor, people in rows:
        totals[actor] = totals.get(actor, 0) + people
        helped += people
    top = None
    if totals:
        top = min(totals, key=lambda actor: (-totals[actor], actor))
    return {'acts': len(rows), 'helped': helped,
            'actors': len(totals), 'top': top}
