"""Row 359 Service Design: exact finite service handoff scheduling.

Schedules supplied service steps with dependency prerequisites and resource
identities. At each step, earliest start is the max of prerequisite finish
and the chosen resource's prior finish. Deterministic first-index ready order.
Caps 32 steps/eight resources/32 prerequisites; includes wait and handoff data.
NOT_CLAIMED: global optimal schedule, customer satisfaction, actual provider
coordination, staffing adequacy, real service execution or deployment.
"""


def service_schedule(durations,resources,prerequisites):
    if any(type(v) not in (list,tuple) for v in (durations,resources,prerequisites)):
        raise TypeError('inputs must be lists or tuples')
    n=len(durations)
    if not 1<=n<=32:raise ValueError('step count must be between 1 and 32')
    if len(resources)!=n or len(prerequisites)!=n:raise ValueError('step shapes must agree')
    for deps in prerequisites:
        if type(deps) not in (list,tuple) or len(deps)>32:raise ValueError('prerequisites must be lists or tuples of at most 32')
    if any(type(v) is not int or not 1<=v<=1000000 for v in durations):raise ValueError('durations must be nonbool integers between 1 and 1000000')
    if any(type(v) is not int or not 0<=v<=7 for v in resources):raise ValueError('resources must be nonbool integers zero through seven')
    for i,deps in enumerate(prerequisites):
        if any(type(j) is not int or not 0<=j<n or j==i for j in deps):raise ValueError('prerequisites must be nonbool valid nonself indices')
        if len(set(deps))!=len(deps):raise ValueError('prerequisites must be unique')
    pending=set(range(n));finished={};resource_free=[0]*8;steps=[]
    while pending:
        ready=[i for i in sorted(pending) if all(j in finished for j in prerequisites[i])]
        if not ready:raise ValueError('prerequisite graph must be acyclic')
        i=ready[0];dependency_finish=max((finished[j] for j in prerequisites[i]),default=0)
        start=max(dependency_finish,resource_free[resources[i]]);end=start+durations[i]
        steps.append({'step_index':i,'resource':resources[i],'start':start,'end':end,'resource_wait':start-dependency_finish})
        finished[i]=end;resource_free[resources[i]]=end;pending.remove(i)
    return {'steps':steps,'makespan':max(finished.values()),'service_execution_performed':False}
