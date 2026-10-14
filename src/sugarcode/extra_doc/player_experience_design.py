"""Row 343 Player Experience Design: finite session activity optimization.

Selects an ordered subsequence of supplied activities to maximize explicit
preference scores under an effort budget. Adjacent selected categories must
differ, providing a supplied-category variety constraint. Up to 12 activities.
Ties prefer lower effort, then lexicographic selected indices.
NOT_CLAIMED: measured engagement, psychological prediction, addictive design,
actual player telemetry, artistic quality or runtime deployment.
"""


def plan_session(activities,effort_budget):
    if type(activities) not in (list,tuple):raise TypeError('activities must be a list or tuple')
    if not 1<=len(activities)<=12:raise ValueError('activity count must be between 1 and 12')
    if any(type(v) not in (list,tuple) or len(v)!=3 for v in activities):
        raise ValueError('activities must contain category effort and preference')
    if type(effort_budget) is not int or not 0<=effort_budget<=1000000:
        raise ValueError('effort_budget must be a nonbool integer zero through 1000000')
    for category,effort,preference in activities:
        if type(category) is not int or not 0<=category<=7:raise ValueError('categories must be nonbool integers zero through seven')
        if type(effort) is not int or not 1<=effort<=1000000:raise ValueError('efforts must be nonbool integers between 1 and 1000000')
        if type(preference) is not int or not 0<=preference<=1000000:raise ValueError('preferences must be nonbool integers zero through 1000000')
    best=None;feasible=0
    for mask in range(1<<len(activities)):
        indices=tuple(i for i in range(len(activities)) if mask&(1<<i))
        chosen=[activities[i] for i in indices]
        if any(a[0]==b[0] for a,b in zip(chosen,chosen[1:])):continue
        effort=sum(a[1] for a in chosen)
        if effort>effort_budget:continue
        feasible+=1;score=sum(a[2] for a in chosen);key=(-score,effort,indices)
        if best is None or key<best:best=key
    negative_score,effort,indices=best
    return {'activity_indices':list(indices),'preference_score':-negative_score,'effort':effort,
            'feasible_count':feasible,'engagement_validated':False}
