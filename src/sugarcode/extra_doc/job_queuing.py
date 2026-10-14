"""Row 644, Job Queuing: a priority queue served by a fixed worker pool.

Jobs are (name, arrival, priority, duration); a lower priority number is more
urgent. Whenever a worker is idle and a job has arrived, the lowest-index idle
worker takes the ready job with the smallest (priority, arrival, input index).
Reported in start order: worker, start, end and wait (start minus arrival), plus
the makespan (0 for no jobs).
Caps (checked before any work): at most 20 jobs, unique names of 1 to 16
characters, arrival 0 to 100, priority 0 to 9, duration 1 to 20, workers 1 to 4,
nonbool ints.
NOT_CLAIMED: preemption, starvation guarantees, persistence, retries, real
queue software, production readiness.
"""
SCOPE = 'PARTIAL: discrete-time priority queue with a fixed pool, no preemption'
NOT_CLAIMED = ('preemption', 'starvation guarantees', 'persistence', 'retries', 'real queue software',
               'production readiness')


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def run_queue(jobs, workers):
    if type(jobs) not in (list, tuple):
        raise TypeError('jobs must be a list or tuple')
    if len(jobs) > 20:
        raise ValueError('jobs must contain at most 20 entries')
    _int(workers, 1, 4, 'workers must be a nonbool integer between 1 and 4')
    for j in jobs:
        if type(j) not in (list, tuple) or len(j) != 4:
            raise ValueError('each job must be a (name, arrival, priority, duration) tuple')
        if type(j[0]) is not str or not 1 <= len(j[0]) <= 16:
            raise ValueError('job names must be strings of 1 to 16 characters')
        _int(j[1], 0, 100, 'arrival must be a nonbool integer between 0 and 100')
        _int(j[2], 0, 9, 'priority must be a nonbool integer between 0 and 9')
        _int(j[3], 1, 20, 'duration must be a nonbool integer between 1 and 20')
    if len({j[0] for j in jobs}) != len(jobs):
        raise ValueError('job names must be unique')
    free, pending, t, out = [0] * workers, list(range(len(jobs))), 0, []
    while pending:
        idle = [w for w in range(workers) if free[w] <= t]
        ready = [i for i in pending if jobs[i][1] <= t]
        if idle and ready:
            i = min(ready, key=lambda k: (jobs[k][2], jobs[k][1], k))
            w = idle[0]
            free[w] = t + jobs[i][3]
            pending.remove(i)
            out.append({'job': jobs[i][0], 'worker': w, 'start': t, 'end': free[w], 'wait': t - jobs[i][1]})
            continue
        t = min([f for f in free if f > t] + [jobs[i][1] for i in pending if jobs[i][1] > t])
    return {'runs': out, 'makespan': max([r['end'] for r in out], default=0)}
