"""Row 249: Bilevel Optimization - Handles hierarchical decisions.

Finite supplied leader options; each induces a strictly convex separable
quadratic follower on a shared box. Solve follower first,then choose leader
by leader fixed+linear follower objective. Unique follower avoids tie policy.
NOT_CLAIMED: continuous leader optimization,general coupled follower QP,
nonunique-response optimistic/pessimistic games,or biological validation.
"""
from fractions import Fraction


def _scalar(v):
    if type(v) not in (int,Fraction):raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('rational values must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:raise ValueError('rational values must fit 32 bits')
    return Fraction(v)


def solve_bilevel(curvature,follower_linear,leader_fixed,leader_linear,lower,upper):
    for seq in (curvature,follower_linear,leader_fixed,leader_linear,lower,upper):
        if type(seq) not in (list,tuple):raise TypeError('inputs must be lists or tuples')
    n=len(curvature);m=len(follower_linear)
    if not 1<=n<=8:raise ValueError('follower dimension count must be between 1 and 8')
    if not 1<=m<=64:raise ValueError('leader option count must be between 1 and 64')
    if len(leader_fixed)!=m or len(leader_linear)!=m or len(lower)!=n or len(upper)!=n:raise ValueError('leader and follower shapes do not match')
    for row in (*follower_linear,*leader_linear):
        if type(row) not in (list,tuple) or len(row)!=n:raise ValueError('objective row must match follower dimension')
    q=[_scalar(v) for v in curvature];b=[[_scalar(v) for v in row] for row in follower_linear];fixed=[_scalar(v) for v in leader_fixed];cost=[[_scalar(v) for v in row] for row in leader_linear];lo=[_scalar(v) for v in lower];hi=[_scalar(v) for v in upper]
    if any(v<=0 for v in q):raise ValueError('follower curvature must be positive')
    if any(a>z for a,z in zip(lo,hi)):raise ValueError('lower bounds must not exceed upper bounds')
    responses=[];leader_values=[];follower_values=[];kkt=[]
    for row,base,leaderrow in zip(b,fixed,cost):
        y=[min(z,max(a,-bi/qi)) for qi,bi,a,z in zip(q,row,lo,hi)]
        gradient=[qi*yi+bi for qi,yi,bi in zip(q,y,row)]
        conditions=[g>=0 if yi==a else g<=0 if yi==z else g==0 for g,yi,a,z in zip(gradient,y,lo,hi)]
        # Equality boxcoordinates have no feasible movement:gradient unrestricted.
        conditions=[True if a==z else flag for a,z,flag in zip(lo,hi,conditions)]
        responses.append(y);leader_values.append(base+sum(a*v for a,v in zip(leaderrow,y)))
        follower_values.append(sum(qi*yi*yi/2+bi*yi for qi,bi,yi in zip(q,row,y)));kkt.append(conditions)
    selected=min(range(m),key=leader_values.__getitem__)
    return {'leader_index':selected,'follower_solution':responses[selected],
            'leader_objective':leader_values[selected],'follower_objective':follower_values[selected],
            'all_follower_responses':responses,'all_leader_objectives':leader_values,
            'follower_kkt':kkt,'general_bilevel_solver_claimed':False}
