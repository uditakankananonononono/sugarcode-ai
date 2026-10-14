"""FLOAT steepest descent on supplied symmetric positive-definite quadratics.
Iterates and line-search arithmetic are IEEE754 float, not exact. Converged means
only computed Euclidean gradient norm <= caller tolerance; no exact optimum proof.
NOT_CLAIMED: arbitrary nonlinear objective; real-world decision; global optimum
of an unknown model; external execution; numerical convergence in every budget.
"""
import math
from fractions import Fraction


def descend(matrix,linear,initial,iterations,tolerance):
    if type(iterations) is not int or not 1<=iterations<=100:raise ValueError('strict iteration count 1..100')
    if type(tolerance) not in (int,float) or not 1e-10<=tolerance<=1 or not math.isfinite(tolerance):raise ValueError('strict finite tolerance 1e-10..1')
    if type(initial) is not list or not 1<=len(initial)<=8:raise ValueError('1..8 initial coordinates before scan')
    d=len(initial)
    def number(v):
        if type(v) not in (int,float) or not -1000<=v<=1000 or not math.isfinite(v):raise ValueError('strict finite quadratic number within -1000..1000')
        return float(v)
    def vector(v):
        if type(v) is not list or len(v)!=d:raise ValueError('one coordinate per dimension')
        return [number(x) for x in v]
    x=vector(initial);b=vector(linear)
    if type(matrix) is not list or len(matrix)!=d:raise ValueError('square matrix dimension')
    a=[vector(row) for row in matrix]
    if any(a[i][j]!=a[j][i] for i in range(d) for j in range(d)):raise ValueError('symmetric quadratic matrix')
    # Exact supplied decimal LDL pivots prove SPD; minimum pivot rejects near-singular work.
    rational=[[Fraction(str(v)) for v in row] for row in matrix];lower=[{} for i in range(d)];pivots=[]
    for i in range(d):
        p=rational[i][i]-sum(lower[i][k]**2*pivots[k] for k in range(i))
        if p<Fraction(1,1000000):raise ValueError('positive definite matrix with LDL pivots at least 1e-6')
        pivots.append(p)
        for j in range(i+1,d):lower[j][i]=(rational[j][i]-sum(lower[j][k]*lower[i][k]*pivots[k] for k in range(i)))/p
    def multiply(v):return [math.fsum(c*z for c,z in zip(row,v)) for row in a]
    def objective(v):return math.fsum([.5*math.fsum(z*q for z,q in zip(v,multiply(v))),math.fsum(c*z for c,z in zip(b,v))])
    history=[objective(x)];steps=[];points=[x[:]]
    for _ in range(iterations):
        g=[v+c for v,c in zip(multiply(x),b)];norm=math.sqrt(math.fsum(v*v for v in g))
        if norm<=tolerance:break
        numerator=math.fsum(v*v for v in g);denominator=math.fsum(v*q for v,q in zip(g,multiply(g)))
        if not math.isfinite(denominator) or denominator<=0:raise ValueError('positive finite numerical curvature required')
        alpha=numerator/denominator;x=[v-alpha*q for v,q in zip(x,g)]
        if any(not math.isfinite(v) for v in x):raise ValueError('finite numerical iterate required')
        steps.append(alpha);points.append(x[:]);history.append(objective(x))
    g=[v+c for v,c in zip(multiply(x),b)];norm=math.sqrt(math.fsum(v*v for v in g))
    return {'point':x,'objective':history[-1],'objective_history':history,'point_history':points,'step_sizes':steps,
            'gradient_norm':norm,'converged':norm<=tolerance,'iterations_used':len(steps),'method':'steepest_descent_exact_quadratic_line_search',
            'objective_definition':'0.5*x^T*A*x + b^T*x','global_optimum_claimed':False,'external_effects':[]}
