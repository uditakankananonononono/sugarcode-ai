"""Cancer Care Coordination.

PARTIAL: caller-declared task dependency/owner readiness ledger, not cancer care,
clinical sequencing, diagnosis, therapy selection or patient-safety assurance.
"""
SCOPE='caller-declared care-task dependency readiness; no clinical care or therapy selection'


def readiness(rows,completed):
    """Rows(task,owner,dependencies),1..32 unique tasks,acyclic known dependencies.

    Textslots exactstr1..40 Unicodeprintable,no casefold/trim/ASCIIguess. Completed
    exactlist/tuple unique known tasks;dependencies exactlist/tuple unique known
    nonself tasks. Mixedrowcontainers accepted. Returnlabel-sorted ready tasks
    (unfinished withall immediate deps completed),blockedtasks/missingdeps,and
    ownerbundles forreadytasks. No implied appointmenttimes,executionorcontacts.
    Callerordering establishes workflow,not medically appropriate ordering.
    """
    def text(x):
        if type(x) is not str or not 1<=len(x)<=40 or not all(ch.isprintable() for ch in x):
            raise ValueError('text must be exactstr printable Unicode length1..40')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=32:raise ValueError('rows must contain1..32 task triples')
    tasks={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('task row must be exactlist/tuple triple')
        task,owner,deps=row;text(task);text(owner)
        if task in tasks:raise ValueError('task labels must be unique')
        if type(deps) not in (list,tuple) or len(deps)>31:raise ValueError('dependencies must be exactlist/tuple atmost31 tasks')
        for dep in deps:text(dep)
        if len(set(deps))!=len(deps) or task in deps:raise ValueError('dependencies must be unique and nonself')
        tasks[task]=(owner,tuple(deps))
    for owner,deps in tasks.values():
        if any(dep not in tasks for dep in deps):raise ValueError('dependencies must refer to known tasks')
    visiting=set();visited=set()
    def visit(task):
        if task in visiting:raise ValueError('task dependencies must be acyclic')
        if task in visited:return
        visiting.add(task)
        for dep in tasks[task][1]:visit(dep)
        visiting.remove(task);visited.add(task)
    for task in tasks:visit(task)
    if type(completed) not in (list,tuple) or len(completed)>32:raise ValueError('completed must be exactlist/tuple atmost32 tasks')
    for task in completed:text(task)
    if len(set(completed))!=len(completed) or any(task not in tasks for task in completed):raise ValueError('completed tasks must be unique and known')
    done=set(completed);ready=[];blocked=[];owners={}
    for task in sorted(tasks):
        if task in done:continue
        owner,deps=tasks[task];missing=tuple(sorted(dep for dep in deps if dep not in done))
        if missing:blocked.append((task,missing))
        else:ready.append(task);owners.setdefault(owner,[]).append(task)
    return {'ready':tuple(ready),'blocked':tuple(blocked),'owners':tuple((owner,tuple(owners[owner])) for owner in sorted(owners)),
            'completed':tuple(sorted(done)),'scope':SCOPE}
