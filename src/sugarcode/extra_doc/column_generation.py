"""Row 242: Column Generation - Handles many variables.

Exact restricted-master/pricing method for min c'x,Ax=b,x>=0 with supplied
nonnegative nonzero columns supplied up front,a feasible initial basis,m<=3,columns<=64.
Returns primal/dual/reduced-cost certificate after all-column pricing.
NOT_CLAIMED: implicit infinite pricing oracles,phase I,general LP dimensions,
unbounded-column models,or biological validation.
"""
from fractions import Fraction
from itertools import combinations


def _scalar(v):
    if type(v) not in (int,Fraction):raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('rational values must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:raise ValueError('rational values must fit 32 bits')
    return Fraction(v)


def _solve(M,rhs):
    rows=[row[:]+[b] for row,b in zip(M,rhs)];n=len(rhs)
    for k in range(n):
        p=next((i for i in range(k,n) if rows[i][k]),None)
        if p is None:return None
        rows[k],rows[p]=rows[p],rows[k];v=rows[k][k];rows[k]=[x/v for x in rows[k]]
        for i in range(n):
            if i!=k:
                v=rows[i][k];rows[i]=[a-v*b for a,b in zip(rows[i],rows[k])]
    return [row[-1] for row in rows]


def generate_columns(columns,costs,demand,initial_basis,max_iterations=64):
    for seq in (columns,costs,demand,initial_basis):
        if type(seq) not in (list,tuple):raise TypeError('inputs must be lists or tuples')
    m=len(demand);n=len(columns)
    if not 1<=m<=3:raise ValueError('row count must be between 1 and 3')
    if not m<=n<=64:raise ValueError('column count must be between row count and 64')
    if len(costs)!=n or len(initial_basis)!=m:raise ValueError('cost and basis shapes do not match')
    if type(max_iterations) is not int or not 1<=max_iterations<=64:raise ValueError('max_iterations must be a nonbool integer between 1 and 64')
    for row in columns:
        if type(row) not in (list,tuple) or len(row)!=m:raise ValueError('column must match row count')
    if any(type(i) is not int or not 0<=i<n for i in initial_basis) or len(set(initial_basis))!=m:raise ValueError('initial basis must contain distinct nonbool column indices')
    cols=[[_scalar(v) for v in col] for col in columns];c=[_scalar(v) for v in costs];b=[_scalar(v) for v in demand]
    if any(v<0 for col in cols for v in col) or any(all(v==0 for v in col) for col in cols):raise ValueError('columns must be nonnegative and nonzero')
    if any(v<0 for v in b):raise ValueError('demand must be nonnegative')
    initial=_solve([[cols[j][i] for j in initial_basis] for i in range(m)],b)
    if initial is None or any(v<0 for v in initial):raise ValueError('initial basis must be nonsingular and feasible')
    active=list(initial_basis);trace=[]
    for iteration in range(max_iterations):
        master=None
        for basis in combinations(active,m):
            M=[[cols[j][i] for j in basis] for i in range(m)];primal=_solve(M,b)
            if primal is None or any(v<0 for v in primal):continue
            dual=_solve([[cols[j][i] for i in range(m)] for j in basis],[c[j] for j in basis])
            if any(c[j]-sum(a*v for a,v in zip(cols[j],dual))<0 for j in active):continue
            master=(basis,primal,dual);break
        if master is None:raise ValueError('restricted master certificate not found')
        basis,primal,dual=master
        reduced=[cj-sum(a*v for a,v in zip(col,dual)) for col,cj in zip(cols,c)]
        entering=min(range(n),key=reduced.__getitem__)
        trace.append({'active_columns':active[:],'dual':dual[:],'minimum_reduced_cost':reduced[entering],'priced_column':entering})
        if reduced[entering]>=0:
            solution=[Fraction(0)]*n
            for j,v in zip(basis,primal):solution[j]=v
            objective=sum(a*v for a,v in zip(c,solution))
            return {'solution':solution,'objective':objective,'dual':dual,'reduced_costs':reduced,'trace':trace,'iterations':iteration+1,'general_lp_solver_claimed':False}
        active.append(entering)
    raise ValueError('column pricing not closed within iteration cap')
