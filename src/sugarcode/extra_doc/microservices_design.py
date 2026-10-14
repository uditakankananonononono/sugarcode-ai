"""Row514 Microservices Design: exact bounded balanced service decomposition.

Partition supplied components into two nonempty services, size at most supplied
cap. Minimize total cross-service coupling; ties lex second-service indices.
Component0 fixed in first service removes label symmetry. Caps12components,
12x12nonnegativeintegercoupling0..1000,2048partitions.
NOT_CLAIMED: deployed microservices, real coupling, network latency, transactions,
team boundaries, architecture suitability or actual system decomposition.
"""


def service_partition(coupling,maximum_size):
    if type(coupling) not in (list,tuple):raise TypeError('coupling must be a list or tuple')
    n=len(coupling)
    if not 2<=n<=12:raise ValueError('component count must be between 2 and 12')
    if any(type(row) not in (list,tuple) or len(row)!=n for row in coupling):raise ValueError('coupling must be square')
    if type(maximum_size) is not int or not 1<=maximum_size<=12:raise ValueError('maximum size must be nonbool integer between 1 and 12')
    if any(type(v) is not int or not 0<=v<=1000 for row in coupling for v in row):raise ValueError('coupling must be nonbool integers zero through 1000')
    best=None;answer=None
    for mask in range(1,1<<(n-1)):
        second=tuple(i for i in range(1,n) if mask>>(i-1)&1);first=tuple(i for i in range(n) if i not in second)
        if len(first)>maximum_size or len(second)>maximum_size:continue
        cost=sum(coupling[i][j]+coupling[j][i] for i in first for j in second);key=(cost,second)
        if best is None or key<best:best=key;answer={'services':[list(first),list(second)],'cross_coupling':cost,'decomposition_performed':False}
    return answer
