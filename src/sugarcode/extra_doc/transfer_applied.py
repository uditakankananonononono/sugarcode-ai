"""Row 835, Transfer - Applies to new contexts: success outside the taught set.

transfer_applied takes taught, a list or tuple of 1 to 6 ASCII strings of 1 to
12 characters, distinct, naming the contexts a skill was taught in, and
trials, a list or tuple of 1 to 8 (context, attempts, successes) tuples.
context is an ASCII string of 1 to 12 characters, distinct across trials.
attempts is a nonbool int from 1 to 10 and successes a nonbool int from 0 to
attempts.
A trial is a new context when its context is not in taught.
Returns new_attempts and new_successes (summed over the new contexts),
familiar_attempts (attempts summed over the taught contexts), new_percent (new
successes as a percent of new attempts, rounded down, 0 when there are no
new attempts) and applied (True when there is at least one new success and
new successes are at least half of new attempts, compared exactly).
Checks, in this order: taught type, taught size, each taught entry, distinct
taught, trials type, trials size, each trial (shape, context, attempts,
successes), distinct contexts.
NOT_CLAIMED: real transfer of learning, learner ability, task similarity,
curriculum fit, production readiness.
"""

SCOPE = 'PARTIAL: tallies supplied trial outcomes in contexts outside a supplied taught list, no learner transfers'
NOT_CLAIMED = ('real transfer of learning', 'learner ability', 'task similarity',
               'curriculum fit', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and 1 <= len(x) <= 12


def transfer_applied(taught, trials):
    if type(taught) not in (list, tuple):
        raise TypeError('taught must be a list or tuple')
    if not 1 <= len(taught) <= 6:
        raise ValueError('taught must contain 1 to 6 entries')
    for t in taught:
        if not _label(t):
            raise ValueError('each taught entry must be an ASCII string of 1 to 12 characters')
    if len(set(taught)) != len(taught):
        raise ValueError('taught entries must be distinct')
    if type(trials) not in (list, tuple):
        raise TypeError('trials must be a list or tuple')
    if not 1 <= len(trials) <= 8:
        raise ValueError('trials must contain 1 to 8 entries')
    rows = []
    for tr in trials:
        if type(tr) not in (list, tuple) or len(tr) != 3:
            raise ValueError('each trial must be a (context, attempts, successes) tuple')
        context, attempts, successes = tr
        if not _label(context):
            raise ValueError('each context must be an ASCII string of 1 to 12 characters')
        if type(attempts) is not int or not 1 <= attempts <= 10:
            raise ValueError('attempts must be a nonbool integer between 1 and 10')
        if type(successes) is not int or not 0 <= successes <= attempts:
            raise ValueError('successes must be a nonbool integer between 0 and attempts')
        rows.append((context, attempts, successes))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('contexts must be distinct')
    new_a = new_s = old_a = 0
    for context, attempts, successes in rows:
        if context in taught:
            old_a += attempts
        else:
            new_a += attempts
            new_s += successes
    return {'new_attempts': new_a, 'new_successes': new_s, 'familiar_attempts': old_a,
            'new_percent': new_s * 100 // new_a if new_a else 0,
            'applied': new_s >= 1 and new_s * 2 >= new_a}
