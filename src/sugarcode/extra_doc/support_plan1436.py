"""Row 1436, Scaffolding: planning support per step from supplied skill demands.

Scaffolding sets the help a learner gets at each step. learner is the
learner's skill level and steps is the list or tuple of skill levels the
steps demand, 1 to 20 of them. learner and every step level are nonbool
ints from 0 to 5 (exact int type). Support at a step is the demand above
the learner's level, never below 0: max(0, step - learner). Reported:
support (the per-step list), total (sum of support), peak (the highest
support, 0 when none is needed), peak_step (position counted from 1 of the
first step with the peak, or None when the peak is 0) and independent
(True when every step needs no support). Checks, in this order: learner,
steps type, steps size, each step level.
NOT_CLAIMED: real learning, learner readiness, support quality, fading
over time, pacing, production readiness.
"""
SCOPE = 'PARTIAL: per-step support arithmetic over supplied levels, no real teaching'
NOT_CLAIMED = ('real learning', 'learner readiness', 'support quality',
               'fading over time', 'pacing', 'production readiness')

MIN_STEPS = 1
MAX_STEPS = 20
MAX_LEVEL = 5


def plan(learner, steps):
    if type(learner) is not int or not 0 <= learner <= MAX_LEVEL:
        raise ValueError('learner must be a nonbool int from 0 to 5')
    if type(steps) not in (list, tuple):
        raise TypeError('steps must be a list or tuple')
    if not MIN_STEPS <= len(steps) <= MAX_STEPS:
        raise ValueError('steps must hold 1 to 20 levels')
    for level in steps:
        if type(level) is not int or not 0 <= level <= MAX_LEVEL:
            raise ValueError('step levels must be nonbool ints from 0 to 5')
    support = [level - learner if level > learner else 0 for level in steps]
    peak = max(support)
    return {'support': support, 'total': sum(support), 'peak': peak,
            'peak_step': support.index(peak) + 1 if peak > 0 else None,
            'independent': peak == 0}
