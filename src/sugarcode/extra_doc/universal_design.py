"""Row 350 Universal Design: exact finite all-profile compatibility selection.

Selects one supplied design candidate satisfying every supplied profile's
maximum effort and required modality availability. Chooses lowest worst-profile
effort, then total effort, then candidate index. Uses explicit profiles only.
Caps 64 candidates/eight profiles; no inferred ability or universal claim.
NOT_CLAIMED: all real-world abilities covered, disability inference, actual
accessibility testing, ethical certification or deployment.
"""


def choose_universal_candidate(efforts,available,maximum_efforts):
    if any(type(v) not in (list,tuple) for v in (efforts,available,maximum_efforts)):
        raise TypeError('inputs must be lists or tuples')
    n=len(efforts);k=len(maximum_efforts)
    if not 1<=n<=64:raise ValueError('candidate count must be between 1 and 64')
    if not 1<=k<=8:raise ValueError('profile count must be between 1 and 8')
    if len(available)!=n:raise ValueError('availability rows must match candidates')
    if any(type(row) not in (list,tuple) or len(row)!=k for row in list(efforts)+list(available)):
        raise ValueError('rows must match profile count')
    if any(type(v) is not int or not 0<=v<=1000000 for row in efforts for v in row):
        raise ValueError('efforts must be nonbool integers zero through 1000000')
    if any(type(v) is not int or v not in (0,1) for row in available for v in row):
        raise ValueError('availability must be nonbool binary integers')
    if any(type(v) is not int or not 0<=v<=1000000 for v in maximum_efforts):
        raise ValueError('maximum efforts must be nonbool integers zero through 1000000')
    feasible=[i for i,row in enumerate(efforts) if all(available[i]) and all(a<=b for a,b in zip(row,maximum_efforts))]
    if not feasible:raise ValueError('no candidate satisfies every supplied profile')
    index=min(feasible,key=lambda i:(max(efforts[i]),sum(efforts[i]),i))
    return {'candidate_index':index,'profile_efforts':list(efforts[index]),'worst_effort':max(efforts[index]),
            'feasible_indices':feasible,'universal_accessibility_validated':False}
