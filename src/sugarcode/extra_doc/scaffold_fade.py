"""Row 739, Scaffolding: support-fading check of supplied support levels.

scaffold_fade takes levels, a list or tuple of 1 to max_steps nonbool ints
from 0 to 5 (the support given at each step, in time order), and max_steps, a
nonbool int from 1 to 20 (default 6). Support should never rise from one
step to the next.
Returns rises (indexes i, counted from 1, where levels[i] > levels[i - 1], in
order), drops (total of the falls levels[i - 1] - levels[i] over the steps
where support falls), final (the last level) and faded (no rise and final
is 0).
Checks, in this order: max_steps, levels type, levels size, each level.
NOT_CLAIMED: real learning, learner readiness, support quality, pacing,
production readiness.
"""
SCOPE = 'PARTIAL: monotone fade check of supplied support levels, no learner is observed'
NOT_CLAIMED = ('real learning', 'learner readiness', 'support quality',
               'pacing', 'production readiness')


def scaffold_fade(levels, max_steps=6):
    if type(max_steps) is not int or not 1 <= max_steps <= 20:
        raise ValueError('max_steps must be a nonbool integer between 1 and 20')
    if type(levels) not in (list, tuple):
        raise TypeError('levels must be a list or tuple')
    if not 1 <= len(levels) <= max_steps:
        raise ValueError('levels must contain 1 to max_steps entries')
    for v in levels:
        if type(v) is not int or not 0 <= v <= 5:
            raise ValueError('each level must be a nonbool integer between 0 and 5')
    rises = []
    drops = 0
    for i in range(1, len(levels)):
        if levels[i] > levels[i - 1]:
            rises.append(i)
        elif levels[i] < levels[i - 1]:
            drops += levels[i - 1] - levels[i]
    final = levels[-1]
    return {'rises': rises, 'drops': drops, 'final': final, 'faded': not rises and final == 0}
