"""Exact scalar quartic trust-region iterations using exact quadratic models.
NOT_CLAIMED: arbitrary multivariate objective; global minimum; authentic model;
runtime integration or external execution.
"""
from fractions import Fraction as F
import math


def _bounded(*values):
    if any(max(v.numerator.bit_length(),v.denominator.bit_length())>4096 for v in values):raise ValueError('trust rational size exceeds 4096 bits')


def optimize(initial,tilt,radius,iterations):
    def num(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded trust number')
        return F(str(v))
    x=num(initial,-10,10);b=num(tilt,-10,10);delta=num(radius,.001,10)
    if type(iterations) is not int or not 1<=iterations<=30:raise ValueError('strict trust iterations 1..30')
    def loss(v):return (v*v-1)**2+b*v
    trace=[];history=[str(loss(x))]
    for t in range(iterations):
        g=4*x*(x*x-1)+b;h=12*x*x-4
        candidates=[-delta,delta,F(0)]
        if h>0 and -delta<=-g/h<=delta:candidates.append(-g/h)
        step=min(candidates,key=lambda p:(g*p+h*p*p/2,p));predicted=-g*step-h*step*step/2
        if predicted<=0:break
        actual=loss(x)-loss(x+step);ratio=actual/predicted;accepted=ratio>F(1,10);old=delta
        if ratio<F(1,4):delta=delta/4
        elif ratio>F(3,4) and abs(step)==old:delta=min(2*delta,F(10))
        if accepted:x+=step
        _bounded(x,g,h,step,predicted,actual,ratio,old,delta,loss(x))
        trace.append({'initial_radius_fraction':str(old),'gradient_fraction':str(g),'hessian_fraction':str(h),'step_fraction':str(step),'predicted_reduction_fraction':str(predicted),
                      'actual_reduction_fraction':str(actual),'ratio_fraction':str(ratio),'accepted':accepted,'point_fraction':str(x),'next_radius_fraction':str(delta)})
        history.append(str(loss(x)))
    return {'point_fraction':str(x),'objective_history_fraction':history,'steps':trace,'iterations_used':len(trace),'global_optimum_claimed':False,'external_effects':[]}
