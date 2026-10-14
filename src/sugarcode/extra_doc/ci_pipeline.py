"""Row 610 continuous integration (PARTIAL): ordering build jobs into parallel stages by their dependencies.

jobs is a list of 1 to 100 (name, needs) pairs: name a unique non-empty string up to 30 characters and needs a
list or tuple of up to 20 distinct names of jobs in the same list. plan(jobs) puts every job into the earliest
stage that comes after all the jobs it needs (stage 1 has jobs with no needs; a job's stage is 1 plus the highest
stage among its needs), listing each stage's names in code-point order. Jobs that sit on a dependency cycle, or
that need a job on one, can never run; they are returned in stuck (code-point order) and the plan is not ok. This
orders jobs on paper; it does not run builds, check that a job's steps work, or estimate how long a stage takes."""

MAX_JOBS = 100
MAX_NAME = 30
MAX_NEEDS = 20
STATUS_NOTE = ("PARTIAL: dependency ordering of supplied job names only; nothing is built or run and no timing "
               "is estimated")


def plan(jobs):
    if not isinstance(jobs, (list, tuple)):
        raise ValueError("jobs: list required")
    if not 1 <= len(jobs) <= MAX_JOBS:
        raise ValueError(f"jobs: 1 to {MAX_JOBS} entries required")
    needs = {}
    for i, job in enumerate(jobs):
        if not isinstance(job, (list, tuple)):
            raise ValueError(f"jobs[{i}]: (name, needs) required")
        if len(job) != 2:
            raise ValueError(f"jobs[{i}]: 2 entries required")
        name, deps = job
        if not isinstance(name, str) or not name or len(name) > MAX_NAME:
            raise ValueError(f"jobs[{i}] name: non-empty string up to {MAX_NAME} characters required")
        if name in needs:
            raise ValueError(f"jobs[{i}] name: duplicate")
        if not isinstance(deps, (list, tuple)):
            raise ValueError(f"jobs[{i}] needs: list required")
        if len(deps) > MAX_NEEDS:
            raise ValueError(f"jobs[{i}] needs: at most {MAX_NEEDS} entries")
        for d in deps:
            if not isinstance(d, str):
                raise ValueError(f"jobs[{i}] needs: names must be strings")
        if len(set(deps)) != len(deps):
            raise ValueError(f"jobs[{i}] needs: duplicate entry")
        needs[name] = list(deps)
    for i, (name, _) in enumerate(jobs):
        for d in needs[name]:
            if d not in needs:
                raise ValueError(f"jobs[{i}] needs: unknown job")
    done = set()
    pending = set(needs)
    stages = []
    while True:
        ready = sorted(n for n in pending if all(d in done for d in needs[n]))
        if not ready:
            break
        done.update(ready)
        pending.difference_update(ready)
        stages.append(ready)
    return {"ok": not pending, "stages": stages, "stuck": sorted(pending), "status_note": STATUS_NOTE}
