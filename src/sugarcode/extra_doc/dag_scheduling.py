"""Row 646, DAG Scheduling: dependency order and parallel stages.

tasks maps a task name to the names it depends on. The order is the
lexicographically smallest topological order (always run the smallest ready
name). The level of a task is 0 with no dependencies, else one more than its
deepest dependency; stages groups names by level, sorted. A cycle (including a
self dependency) raises.
Caps (checked before any work): 1 to 30 tasks, names of 1 to 16 characters,
dependencies a list or tuple of unique declared names.
NOT_CLAIMED: durations or critical-path time, resource limits, execution,
dynamic graphs, real schedulers, production readiness.
"""
SCOPE = 'PARTIAL: static dependency graph ordering and level grouping only'
NOT_CLAIMED = ('durations or critical path time', 'resource limits', 'execution', 'dynamic graphs',
               'real schedulers', 'production readiness')


def dag_schedule(tasks):
    if type(tasks) is not dict:
        raise TypeError('tasks must be a dict')
    if not 1 <= len(tasks) <= 30:
        raise ValueError('tasks must contain between 1 and 30 entries')
    for name, deps in tasks.items():
        if type(name) is not str or not 1 <= len(name) <= 16:
            raise ValueError('task names must be strings of 1 to 16 characters')
        if type(deps) not in (list, tuple):
            raise TypeError('dependencies must be a list or tuple')
        if any(type(d) is not str or d not in tasks for d in deps):
            raise ValueError('dependencies must be declared tasks')
        if len(set(deps)) != len(deps):
            raise ValueError('dependencies must be unique')
    left = {n: set(d) for n, d in tasks.items()}
    order, level = [], {}
    while left:
        ready = sorted(n for n, d in left.items() if not d)
        if not ready:
            raise ValueError('dependency graph contains a cycle')
        n = ready[0]
        level[n] = 1 + max((level[d] for d in tasks[n]), default=-1)
        order.append(n)
        del left[n]
        for d in left.values():
            d.discard(n)
    top = max(level.values())
    stages = [sorted(n for n in level if level[n] == k) for k in range(top + 1)]
    return {'order': order, 'levels': level, 'stages': stages}
