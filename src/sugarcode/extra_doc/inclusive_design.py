"""Row 349 Inclusive Design: exact finite perspective-coverage selection.

Selects supplied design features covering every explicitly supplied perspective
at least a requested count, minimizing total supplied cost. Reports covered
perspectives and selected features, not inferred demographic representation.
Caps 12 features/eight perspectives, at most 4096 feature subsets.
NOT_CLAIMED: real diversity validation, inferred sensitive traits, universal
representation, actual consultation, ethical certification or deployment.
"""


def inclusive_features(coverage,costs,minimum_counts):
    if any(type(v) not in (list,tuple) for v in (coverage,costs,minimum_counts)):
        raise TypeError('inputs must be lists or tuples')
    n=len(coverage);k=len(minimum_counts)
    if not 1<=n<=12:raise ValueError('feature count must be between 1 and 12')
    if not 1<=k<=8:raise ValueError('perspective count must be between 1 and 8')
    if len(costs)!=n:raise ValueError('cost count must match features')
    if any(type(row) not in (list,tuple) or len(row)!=k for row in coverage):
        raise ValueError('coverage rows must match perspectives')
    if any(type(v) is not int or v not in (0,1) for row in coverage for v in row):
        raise ValueError('coverage must be nonbool binary integers')
    if any(type(v) is not int or not 0<=v<=1000000 for v in costs):
        raise ValueError('costs must be nonbool integers zero through 1000000')
    if any(type(v) is not int or not 0<=v<=n for v in minimum_counts):
        raise ValueError('minimum counts must be nonbool integers inside feature range')
    best=None;feasible=0
    for mask in range(1<<n):
        chosen=tuple(i for i in range(n) if mask&(1<<i))
        counts=[sum(coverage[i][j] for i in chosen) for j in range(k)]
        if any(a<b for a,b in zip(counts,minimum_counts)):continue
        feasible+=1;cost=sum(costs[i] for i in chosen);key=(cost,len(chosen),chosen)
        if best is None or key<best[0]:best=(key,counts)
    if best is None:raise ValueError('no feature selection covers supplied perspectives')
    (cost,length,chosen),counts=best
    return {'feature_indices':list(chosen),'coverage_counts':counts,'cost':cost,
            'feasible_count':feasible,'representation_validated':False}
