"""Row 639, Runbook Creation: ordering the steps of a supplied runbook.

runbook_steps takes steps, a list or tuple of 1 to 20 (name, needs) pairs.
name is a string of 1 to 16 characters, unique across steps. needs is a list
or tuple of 0 to 4 distinct step names that must run first. The order is
built by repeatedly taking the first listed step whose needs are all done.
Reported: order (step names), depth (name to 1 plus the largest depth of its
needs, 1 for a step with no needs) and max_depth.
Checks, in this order: steps type, steps size, then per step the pair shape,
name, duplicate name, needs type, needs size, each need and duplicate need;
then an unknown need, then a cycle (a step needing itself is a cycle).
NOT_CLAIMED: running commands, access control, approvals, versioning,
rollback, production readiness.
"""
SCOPE = 'PARTIAL: dependency ordering of supplied runbook steps, nothing executed'
NOT_CLAIMED = ('running commands', 'access control', 'approvals', 'versioning',
               'rollback', 'production readiness')

MAX_STEPS = 20
MAX_NEEDS = 4


def runbook_steps(steps):
    if type(steps) not in (list, tuple):
        raise TypeError('steps must be a list or tuple')
    if not 1 <= len(steps) <= MAX_STEPS:
        raise ValueError('steps must contain 1 to 20 entries')
    names = []
    needs_of = {}
    for s in steps:
        if type(s) not in (list, tuple) or len(s) != 2:
            raise ValueError('each step must be a (name, needs) pair')
        name, needs = s
        if type(name) is not str or not 1 <= len(name) <= 16:
            raise ValueError('step names must be strings of 1 to 16 characters')
        if name in needs_of:
            raise ValueError('duplicate step name')
        if type(needs) not in (list, tuple):
            raise TypeError('needs must be a list or tuple')
        if len(needs) > MAX_NEEDS:
            raise ValueError('needs must contain at most 4 entries')
        seen = []
        for n in needs:
            if type(n) is not str or not 1 <= len(n) <= 16:
                raise ValueError('needs must be strings of 1 to 16 characters')
            if n in seen:
                raise ValueError('duplicate need')
            seen.append(n)
        names.append(name)
        needs_of[name] = seen
    for name in names:
        for n in needs_of[name]:
            if n not in needs_of:
                raise ValueError('unknown step in needs')
    order, done, depth = [], set(), {}
    while len(order) < len(names):
        for name in names:
            if name not in done and all(n in done for n in needs_of[name]):
                break
        else:
            raise ValueError('steps contain a cycle')
        order.append(name)
        done.add(name)
        depth[name] = 1 + max((depth[n] for n in needs_of[name]), default=0)
    return {'order': order, 'depth': depth, 'max_depth': max(depth.values())}
