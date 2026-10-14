"""Row 643, Resource Scheduling: greedy list scheduling of jobs onto machines.

Jobs are taken in the given order. Each goes to the machine with the smallest
current load (lowest index on ties) and runs right after that machine's last job.
Reported: assignments with machine, start and end, final loads, and makespan.
Caps (checked before any work): at most 30 jobs, unique names of 1 to 16
characters, durations 1 to 1000, machines 1 to 8, nonbool ints.
NOT_CLAIMED: optimal makespan, job priorities or deadlines, preemption,
heterogeneous machines, real compute allocation, production readiness.
"""
SCOPE = 'PARTIAL: in-order least-loaded greedy assignment on identical machines'
NOT_CLAIMED = ('optimal makespan', 'priorities or deadlines', 'preemption', 'heterogeneous machines',
               'real compute allocation', 'production readiness')


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def schedule_jobs(jobs, machines):
    if type(jobs) not in (list, tuple):
        raise TypeError('jobs must be a list or tuple')
    if len(jobs) > 30:
        raise ValueError('jobs must contain at most 30 entries')
    _int(machines, 1, 8, 'machines must be a nonbool integer between 1 and 8')
    for j in jobs:
        if type(j) not in (list, tuple) or len(j) != 2:
            raise ValueError('each job must be a (name, duration) pair')
        if type(j[0]) is not str or not 1 <= len(j[0]) <= 16:
            raise ValueError('job names must be strings of 1 to 16 characters')
        _int(j[1], 1, 1000, 'duration must be a nonbool integer between 1 and 1000')
    if len({j[0] for j in jobs}) != len(jobs):
        raise ValueError('job names must be unique')
    loads, out = [0] * machines, []
    for name, dur in jobs:
        k = min(range(machines), key=lambda i: (loads[i], i))
        out.append({'job': name, 'machine': k, 'start': loads[k], 'end': loads[k] + dur})
        loads[k] += dur
    return {'assignments': out, 'loads': loads, 'makespan': max(loads)}
