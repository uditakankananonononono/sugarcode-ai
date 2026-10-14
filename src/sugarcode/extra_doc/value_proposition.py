"""Row 363 Value Proposition Design: exact finite need-covering offer selection.

Choose supplied features to maximize total covered need importance under cost
budget; count a need once. Ties: lower cost, fewer features, lexicographic tuple.
Caps 12 features, 16 needs, 4096 subsets; costs/importance/budget 0..1000000.
NOT_CLAIMED: compelling customer response, researched customer needs, pricing
validation, sales conversion, real offer delivery or natural-language marketing.
"""


def design_offer(costs,coverage,importance,budget):
    if any(type(v) not in (list,tuple) for v in (costs,coverage,importance)):
        raise TypeError('inputs must be lists or tuples')
    n=len(costs);m=len(importance)
    if not 1<=n<=12 or not 1<=m<=16:raise ValueError('feature count must be 1..12 and need count 1..16')
    if len(coverage)!=n or any(type(row) not in (list,tuple) or len(row)>16 for row in coverage):
        raise ValueError('coverage rows must match features and contain at most 16 indices')
    if any(type(v) is not int or not 0<=v<=1000000 for v in [*costs,*importance,budget]):
        raise ValueError('costs importance and budget must be nonbool integers zero through 1000000')
    for row in coverage:
        if any(type(j) is not int or not 0<=j<m for j in row):raise ValueError('need indices must be nonbool valid indices')
        if len(set(row))!=len(row):raise ValueError('need indices must be unique')
    best=None;answer=None
    for mask in range(1<<n):
        chosen=tuple(i for i in range(n) if mask>>i&1)
        cost=sum(costs[i] for i in chosen)
        if cost>budget:continue
        covered=sorted({j for i in chosen for j in coverage[i]})
        benefit=sum(importance[j] for j in covered);key=(-benefit,cost,len(chosen),chosen)
        if best is None or key<best:
            best=key;answer={'feature_indices':list(chosen),'covered_needs':covered,'importance':benefit,'cost':cost}
    return {**answer,'customer_response_validated':False}
