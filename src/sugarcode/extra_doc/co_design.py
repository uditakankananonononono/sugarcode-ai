"""Row 352 Co-Design: exact finite stakeholder-consensus design selection.

Chooses a supplied design candidate meeting every stakeholder's minimum
utility. Maximizes minimum stakeholder surplus, then total surplus, then first
candidate index. Returns stakeholder-specific reasons as numeric certificates.
Caps 64 candidates/eight stakeholders with integer utilities -1000..1000.
NOT_CLAIMED: actual stakeholder collaboration, consent, interpersonal agreement,
preferences inferred from identity, fairness legitimacy or deployment.
"""


def consensus_design(utilities,minimum_utilities):
    if type(utilities) not in (list,tuple) or type(minimum_utilities) not in (list,tuple):
        raise TypeError('utilities and minimums must be lists or tuples')
    n=len(utilities);k=len(minimum_utilities)
    if not 1<=n<=64:raise ValueError('candidate count must be between 1 and 64')
    if not 1<=k<=8:raise ValueError('stakeholder count must be between 1 and 8')
    if any(type(row) not in (list,tuple) or len(row)!=k for row in utilities):
        raise ValueError('utility rows must match stakeholders')
    if any(type(v) is not int or not -1000<=v<=1000 for row in utilities for v in row):
        raise ValueError('utilities must be nonbool integers between -1000 and 1000')
    if any(type(v) is not int or not -1000<=v<=1000 for v in minimum_utilities):
        raise ValueError('minimums must be nonbool integers between -1000 and 1000')
    best=None;feasible=[]
    for index,row in enumerate(utilities):
        surplus=[a-b for a,b in zip(row,minimum_utilities)]
        if any(v<0 for v in surplus):continue
        feasible.append(index);key=(-min(surplus),-sum(surplus),index)
        if best is None or key<best[0]:best=(key,surplus)
    if best is None:raise ValueError('no design meets every stakeholder minimum')
    key,surplus=best
    return {'candidate_index':key[2],'stakeholder_surpluses':surplus,'minimum_surplus':-key[0],
            'total_surplus':-key[1],'feasible_indices':feasible,'collaboration_performed':False}
