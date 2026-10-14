"""Row 645, Workflow Orchestration: ordered steps with per-step failure policy.

Steps run in order. A step named in failing is marked failed; if its policy is
abort, every later step is not_run, if its policy is continue the workflow goes
on. Overall result: aborted (an abort step failed), completed_with_failures (some
failed, none aborted), or succeeded.
Caps (checked before any work): 1 to 20 steps, unique names of 1 to 16
characters, policy abort or continue, failing a list or tuple of unique declared
step names.
NOT_CLAIMED: parallel branches (see DAG Scheduling), retries, timeouts, state
persistence, real task execution, production readiness.
"""
SCOPE = 'PARTIAL: sequential steps with abort or continue on scripted failures'
NOT_CLAIMED = ('parallel branches', 'retries', 'timeouts', 'state persistence', 'real task execution',
               'production readiness')


def run_workflow(steps, failing=()):
    if type(steps) not in (list, tuple):
        raise TypeError('steps must be a list or tuple')
    if not 1 <= len(steps) <= 20:
        raise ValueError('steps must contain between 1 and 20 entries')
    for s in steps:
        if type(s) not in (list, tuple) or len(s) != 2:
            raise ValueError('each step must be a (name, policy) pair')
        if type(s[0]) is not str or not 1 <= len(s[0]) <= 16:
            raise ValueError('step names must be strings of 1 to 16 characters')
        if type(s[1]) is not str or s[1] not in ('abort', 'continue'):
            raise ValueError('policy must be abort or continue')
    names = [s[0] for s in steps]
    if len(set(names)) != len(names):
        raise ValueError('step names must be unique')
    if type(failing) not in (list, tuple):
        raise TypeError('failing must be a list or tuple')
    if any(type(f) is not str or f not in names for f in failing) or len(set(failing)) != len(failing):
        raise ValueError('failing must be unique declared step names')
    statuses, aborted = [], False
    for name, policy in steps:
        if aborted:
            statuses.append((name, 'not_run'))
        elif name in failing:
            statuses.append((name, 'failed'))
            aborted = policy == 'abort'
        else:
            statuses.append((name, 'ok'))
    if aborted:
        overall = 'aborted'
    elif any(st == 'failed' for _, st in statuses):
        overall = 'completed_with_failures'
    else:
        overall = 'succeeded'
    return {'statuses': statuses, 'overall': overall}
