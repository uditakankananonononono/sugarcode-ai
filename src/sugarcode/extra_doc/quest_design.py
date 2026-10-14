"""Row 341 Quest Design: finite dependency-ordered objective generation.

Generates an ordered quest plan from supplied objective labels, prerequisite
indices and positive effort costs. Selects all ancestors of a target, excludes
unrelated objectives, and topologically schedules first-index ready objectives.
NOT_CLAIMED: narrative meaning, invented objectives, player enjoyment,
branching story quality, runtime game execution or deployment.
"""


def quest_plan(labels,prerequisites,efforts,target):
    if any(type(v) not in (list,tuple) for v in (labels,prerequisites,efforts)):
        raise TypeError('inputs must be lists or tuples')
    n=len(labels)
    if not 1<=n<=32:raise ValueError('objective count must be between 1 and 32')
    if len(prerequisites)!=n or len(efforts)!=n:raise ValueError('objective shapes must agree')
    if type(target) is not int or not 0<=target<n:raise ValueError('target must be a nonbool objective index')
    for deps in prerequisites:
        if type(deps) not in (list,tuple) or len(deps)>32:raise ValueError('prerequisite lists must not exceed 32 indices')
    for label in labels:
        if type(label) is not str:raise TypeError('labels must be strings')
        if not 1<=len(label)<=80:raise ValueError('label length must be between 1 and 80')
        if not label.strip():raise ValueError('labels must not be blank')
    if any(type(v) is not int or not 1<=v<=1000000 for v in efforts):raise ValueError('efforts must be nonbool integers between 1 and 1000000')
    for i,deps in enumerate(prerequisites):
        if any(type(j) is not int or not 0<=j<n or j==i for j in deps):raise ValueError('prerequisites must be nonbool valid nonself indices')
        if len(set(deps))!=len(deps):raise ValueError('prerequisites must be unique')
    # Validate the full supplied graph, not only the target's ancestry.
    pending=set(range(n));global_order=[]
    while pending:
        ready=[i for i in sorted(pending) if all(j not in pending for j in prerequisites[i])]
        if not ready:raise ValueError('prerequisite graph must be acyclic')
        i=ready[0];pending.remove(i);global_order.append(i)
    needed={target};stack=[target]
    while stack:
        for j in prerequisites[stack.pop()]:
            if j not in needed:needed.add(j);stack.append(j)
    order=[i for i in global_order if i in needed];elapsed=0;steps=[]
    for i in order:
        steps.append({'objective_index':i,'label':labels[i],'start_effort':elapsed,'end_effort':elapsed+efforts[i]})
        elapsed+=efforts[i]
    return {'objective_indices':order,'steps':steps,'total_effort':elapsed,'meaning_validated':False}
