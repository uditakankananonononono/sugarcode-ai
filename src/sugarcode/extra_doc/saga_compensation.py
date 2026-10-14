"""Row 650, Saga Pattern: compensation plan for a supplied saga run.

run_saga takes steps, a list or tuple of 1 to 10
(name, undoable) pairs: name a string of 1 to 16 characters, unique across
steps, undoable a real bool. fail_at is None (nothing fails) or a nonbool
int from 0 to len(steps) - 1 naming the step that fails. Steps run in order;
the failing step does not count as done. After a failure the done steps are
compensated in reverse order when undoable, and the others are reported as
stuck. Reported: status ('completed' with no failure, 'compensated' when
every done step was undone, 'stuck' otherwise), done (names), failed (the
failing name or None), compensated (names in the order undone) and stuck
(names, in reverse order).
Checks, in this order: steps type, steps size, fail_at, then per step the pair
shape, name, duplicate name and undoable flag.
NOT_CLAIMED: calling services, retries, persistence, concurrency, timeouts,
production readiness.
"""
SCOPE = 'PARTIAL: compensation planning for a supplied saga, no services called'
NOT_CLAIMED = ('calling services', 'retries', 'persistence', 'concurrency', 'timeouts',
               'production readiness')

MAX_STEPS = 10


def run_saga(steps, fail_at=None):
    if type(steps) not in (list, tuple):
        raise TypeError('steps must be a list or tuple')
    if not 1 <= len(steps) <= MAX_STEPS:
        raise ValueError('steps must contain 1 to 10 entries')
    if fail_at is not None and (type(fail_at) is not int or not 0 <= fail_at < len(steps)):
        raise ValueError('fail_at must be None or a nonbool integer index of a step')
    seen = set()
    for s in steps:
        if type(s) not in (list, tuple) or len(s) != 2:
            raise ValueError('each step must be a (name, undoable) pair')
        name, undoable = s
        if type(name) is not str or not 1 <= len(name) <= 16:
            raise ValueError('step names must be strings of 1 to 16 characters')
        if name in seen:
            raise ValueError('duplicate step name')
        seen.add(name)
        if type(undoable) is not bool:
            raise ValueError('undoable must be a bool')
    if fail_at is None:
        return {'status': 'completed', 'done': [s[0] for s in steps], 'failed': None,
                'compensated': [], 'stuck': []}
    done = steps[:fail_at]
    compensated = [s[0] for s in reversed(done) if s[1]]
    stuck = [s[0] for s in reversed(done) if not s[1]]
    return {'status': 'stuck' if stuck else 'compensated', 'done': [s[0] for s in done],
            'failed': steps[fail_at][0], 'compensated': compensated, 'stuck': stuck}
