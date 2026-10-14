"""Exact constraint generation for finite convex max-affine scalar objectives.
NOT_CLAIMED: arbitrary continuous oracle; authentic model; scalable LP solver;
runtime integration or external execution.
"""
from fractions import Fraction as F
import math


def solve(planes,bounds,iterations):
    if type(planes) is not list or not 1<=len(planes)<=40:raise ValueError('1..40 affine planes before scan')
    def num(v):
        if type(v) not in (int,float) or not -1000<=v<=1000 or not math.isfinite(v):raise ValueError('strict finite cutting number -1000..1000')
        return F(str(v))
    if type(bounds) is not list or len(bounds)!=2:raise ValueError('two cutting interval bounds')
    lo,hi=map(num,bounds)
    if lo>hi:raise ValueError('ordered cutting bounds')
    data=[]
    for row in planes:
        if type(row) is not list or len(row)!=2:raise ValueError('affine plane slope and intercept pair')
        data.append(tuple(map(num,row)))
    if type(iterations) is not int or not 1<=iterations<=40:raise ValueError('strict cutting iterations 1..40')
    active=[0];trace=[];converged=False
    def value(i,x):a,b=data[i];return a*x+b
    for _ in range(iterations):
        points={lo,hi}
        for i in active:
            for j in active:
                a,b=data[i];c,d=data[j]
                if a!=c:
                    x=(d-b)/(a-c)
                    if lo<=x<=hi:points.add(x)
        x=min(points,key=lambda x:(max(value(i,x) for i in active),x));lower=max(value(i,x) for i in active)
        witness=max(range(len(data)),key=lambda i:(value(i,x),-i));upper=value(witness,x);gap=upper-lower
        trace.append({'active_plane_indices':active[:],'point_fraction':str(x),'lower_bound_fraction':str(lower),'objective_fraction':str(upper),'gap_fraction':str(gap),'separating_plane_index':witness})
        if gap==0:converged=True;break
        active.append(witness)
    return {'point_fraction':str(x),'objective_fraction':str(upper),'lower_bound_fraction':str(lower),'gap_fraction':str(gap),
            'converged_exact_in_supplied_model':converged,'trace':trace,'iterations_used':len(trace),'external_effects':[]}
