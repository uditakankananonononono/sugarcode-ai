"""FLOAT synchronous SIR hazard-flow simulation conserving compartment mass.
NOT_CLAIMED: exact SIR ODE solution; actual epidemic forecast; authentic rates;
parameter fitting; external execution; runtime integration.
"""
import math


def simulate(susceptible,infected,recovered,beta,gamma,dt,steps):
    def number(v,lower,upper,field):
        if type(v) not in (int,float) or not lower<=v<=upper or not math.isfinite(v):raise ValueError('strict finite bounded '+field)
        return float(v)
    s=number(susceptible,0,1000000,'compartment');i=number(infected,0,1000000,'compartment');r=number(recovered,0,1000000,'compartment')
    n=s+i+r
    if not 0<n<=1000000:raise ValueError('positive total population at most 1000000')
    b=number(beta,0,1000,'beta');g=number(gamma,0,1000,'gamma');h=number(dt,1e-6,10,'dt')
    if type(steps) is not int or not 0<=steps<=1000:raise ValueError('strict integer steps 0..1000')
    curve=[{'time':0.0,'susceptible':s,'infected':i,'recovered':r,'new_infections':0.0,'new_recoveries':0.0}]
    for k in range(1,steps+1):
        # Both flows use old compartments: newly infected cannot recover same step.
        infection=s*(-math.expm1(-b*i/n*h));recovery=i*(-math.expm1(-g*h))
        s-=infection;i+=infection-recovery;r+=recovery
        curve.append({'time':k*h,'susceptible':s,'infected':i,'recovered':r,'new_infections':infection,'new_recoveries':recovery})
    return {'curve':curve,'population':n,'units':'compartment counts; beta/gamma inverse time; dt time units',
            'method':'synchronous exponential hazard flows, discrete approximation, not exact SIR ODE solution',
            'real_epidemic_forecast_verified':False,'parameters_fitted':False,'external_effects':[],
            'assumptions':['closed homogeneous population, no births/deaths/reinfection',
                           'supplied rates constant; mixing and parameter truth unverified']}
