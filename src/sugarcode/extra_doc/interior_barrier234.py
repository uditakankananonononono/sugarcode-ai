"""FLOAT separable box log-barrier interior-point Newton path.
NOT_CLAIMED: exact optimum; arbitrary inequalities; full convergence; authentic
model; runtime integration or external execution.
"""
import math


def optimize(diagonal,linear,lower,upper,initial,barriers,newton_steps):
    if type(initial) is not list or not 1<=len(initial)<=8:raise ValueError('1..8 interior coordinates before scan')
    n=len(initial)
    def num(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded interior number')
        return float(v)
    def vector(row,lo):
        if type(row) is not list or len(row)!=n:raise ValueError('one interior value per dimension')
        return [num(v,lo,100) for v in row]
    a=vector(diagonal,.001);b=vector(linear,-100);lo=vector(lower,-100);hi=vector(upper,-100);x=vector(initial,-100)
    if any(not l<v<u or u-l<.001 for l,v,u in zip(lo,x,hi)):raise ValueError('strict interior point with box width at least .001')
    if type(barriers) is not list or not 1<=len(barriers)<=10:raise ValueError('1..10 barriers before scan')
    mus=[num(v,.000001,100) for v in barriers]
    if any(next_mu>=mu for mu,next_mu in zip(mus,mus[1:])):raise ValueError('strict decreasing positive barriers')
    if type(newton_steps) is not int or not 1<=newton_steps<=20:raise ValueError('strict interior Newton steps 1..20')
    def loss(v):return math.fsum(.5*q*z*z+c*z for q,c,z in zip(a,b,v))
    def barrier(v,mu):return loss(v)-mu*math.fsum(math.log(z-l)+math.log(u-z) for z,l,u in zip(v,lo,hi))
    trace=[]
    for mu in mus:
        for k in range(newton_steps):
            g=[q*z+c-mu/(z-l)+mu/(u-z) for q,c,z,l,u in zip(a,b,x,lo,hi)]
            h=[q+mu/(z-l)**2+mu/(u-z)**2 for q,z,l,u in zip(a,x,lo,hi)];p=[-v/q for v,q in zip(g,h)]
            if max(abs(v) for v in g)<=1e-8:break
            alpha=1.
            for z,v,l,u in zip(x,p,lo,hi):
                if v>0:alpha=min(alpha,.99*(u-z)/v)
                elif v<0:alpha=min(alpha,.99*(l-z)/v)
            old=barrier(x,mu);dot=math.fsum(v*q for v,q in zip(g,p));candidate=None
            for attempt in range(40):
                trial=[z+alpha*v for z,v in zip(x,p)]
                if all(l<z<u for z,l,u in zip(trial,lo,hi)) and barrier(trial,mu)<=old+.0001*alpha*dot:candidate=trial;break
                alpha/=2
            if candidate is None:raise ValueError('interior Armijo step not found within 40 reductions')
            before=x[:];x=candidate
            trace.append({'barrier':mu,'gradient':g,'hessian_diagonal':h,'direction':p,'step_size':alpha,'point_before':before,'point':x[:],
                          'barrier_objective_before':old,'barrier_objective_after':barrier(x,mu),'objective':loss(x)})
    return {'point':x,'objective':loss(x),'slacks_lower':[v-l for v,l in zip(x,lo)],'slacks_upper':[u-v for u,v in zip(hi,x)],
            'barrier_path':mus,'steps':trace,'strict_interior':all(l<v<u for l,v,u in zip(lo,x,hi)),'global_optimum_claimed':False,'external_effects':[]}
