"""FLOAT Adam solver for supplied positive diagonal quadratic objectives.
NOT_CLAIMED: arbitrary objective; global convergence; real-world execution;
authentic model or gradients; runtime integration; exact arithmetic.
"""
import math


def optimize(diagonal,linear,initial,rate,beta1,beta2,epsilon,iterations):
    if type(iterations) is not int or not 1<=iterations<=100:raise ValueError('strict Adam iterations 1..100')
    def numeric(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded Adam number')
        return float(v)
    lr=numeric(rate,1e-10,1);b1=numeric(beta1,0,.99);b2=numeric(beta2,0,.999);eps=numeric(epsilon,1e-10,1)
    if type(initial) is not list or not 1<=len(initial)<=8:raise ValueError('1..8 Adam coordinates before scan')
    d=len(initial)
    def vector(v,lo,hi):
        if type(v) is not list or len(v)!=d:raise ValueError('one Adam value per coordinate')
        return [numeric(z,lo,hi) for z in v]
    x=vector(initial,-1000,1000);a=vector(diagonal,.000001,1000);b=vector(linear,-1000,1000)
    m=[0.]*d;v=[0.]*d;trace=[]
    def loss(x):return math.fsum(.5*q*z*z+c*z for q,c,z in zip(a,b,x))
    history=[loss(x)]
    for t in range(1,iterations+1):
        g=[q*z+c for q,z,c in zip(a,x,b)]
        m=[b1*old+(1-b1)*grad for old,grad in zip(m,g)]
        v=[b2*old+(1-b2)*grad*grad for old,grad in zip(v,g)]
        mh=[z/(1-b1**t) for z in m];vh=[z/(1-b2**t) for z in v]
        scales=[lr/(math.sqrt(z)+eps) for z in vh]
        x=[z-scale*grad for z,scale,grad in zip(x,scales,mh)]
        trace.append({'step':t,'gradient':g,'first_moment':m[:],'second_moment':v[:],'corrected_first_moment':mh,'corrected_second_moment':vh,'coordinate_learning_rates':scales,'point':x[:]})
        history.append(loss(x))
    return {'point':x,'objective_history':history,'steps':trace,'iterations_used':iterations,
            'final_gradient':[q*z+c for q,z,c in zip(a,x,b)],'method':'Adam_diagonal_quadratic_FLOAT',
            'objective_definition':'sum(0.5*a_i*x_i^2 + b_i*x_i)','global_convergence_claimed':False,'external_effects':[]}
