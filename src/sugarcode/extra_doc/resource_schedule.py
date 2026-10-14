"""Row 573, Scheduling System: exact assignment of tasks to identical machines with the smallest finishing time.

assign_tasks(durations, machines) takes the length of each task and the number of identical machines, runs no task in
parts and no two tasks at once on one machine, and returns, exactly:
  makespan    the smallest possible time at which the last machine finishes;
  assignment  for each task (in the order given) the machine number that runs it, numbered from 0 in order of first
              use (a task never uses machine k before some earlier task used machine k-1); among all assignments
              that reach the makespan it is the one that reads smallest from the left;
  loads       the total time on each of the machines (length machines, unused machines show 0).
Caps: durations a list or tuple of 1 to 10 nonbool ints, each 1 to 1000; machines a nonbool int, 1 to 5.
Order of checks: durations (type, count, then each value in order: type, range), then machines (type, range), and only
then any search is run. The minimum is found by exact dynamic programming over subsets of tasks; the assignment is then
found by a depth-first search that tries machine numbers in increasing order.

NOT_CLAIMED: arithmetic on the numbers supplied only. It does not say the durations are right, that real machines are
identical or never break, that tasks have no order or set-up time, or that the makespan is the right thing to
minimise; no due dates, costs or priorities are considered. No clinical or wet-lab claim.
"""

MAX_TASKS = 10
MAX_MACHINES = 5
MAX_DURATION = 1000


def _int(v, what):
    if type(v) is not int:
        raise TypeError(what + ' must be a nonbool int')
    return v


def assign_tasks(durations, machines):
    if type(durations) not in (list, tuple):
        raise TypeError('durations must be a list or tuple')
    if not 1 <= len(durations) <= MAX_TASKS:
        raise ValueError('task count must be between 1 and 10')
    ds = []
    for d in durations:
        v = _int(d, 'duration')
        if not 1 <= v <= MAX_DURATION:
            raise ValueError('duration must be between 1 and 1000')
        ds.append(v)
    m = _int(machines, 'machines')
    if not 1 <= m <= MAX_MACHINES:
        raise ValueError('machines must be between 1 and 5')
    n = len(ds)
    full = (1 << n) - 1
    total = [0] * (full + 1)
    for mask in range(1, full + 1):
        low = mask & -mask
        total[mask] = total[mask ^ low] + ds[low.bit_length() - 1]
    best = total[:]                       # best[mask]: smallest makespan of the tasks in mask on 1 machine
    for _ in range(m - 1):
        nxt = best[:]
        for mask in range(1, full + 1):
            sub = mask
            while sub:
                v = max(total[sub], best[mask ^ sub])
                if v < nxt[mask]:
                    nxt[mask] = v
                sub = (sub - 1) & mask
        best = nxt
    limit = best[full]
    loads = [0] * m
    assign = [0] * n
    dead = set()

    def dfs(i, used):
        if i == n:
            return True
        key = (i, tuple(loads[:used]), used)
        if key in dead:
            return False
        for k in range(min(used + 1, m)):
            if loads[k] + ds[i] <= limit:
                loads[k] += ds[i]
                assign[i] = k
                if dfs(i + 1, max(used, k + 1)):
                    return True
                loads[k] -= ds[i]
        dead.add(key)
        return False
    dfs(0, 0)
    return {'makespan': limit, 'assignment': assign, 'loads': loads}
