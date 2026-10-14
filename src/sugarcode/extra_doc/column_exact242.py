"""Exact finite-column convex-mixture LP generation with dual pricing.
NOT_CLAIMED: implicit infinite columns; large-variable scalability; authentic
model; external execution or runtime integration.
"""
from fractions import Fraction as F
import math
from itertools import combinations


def solve(columns,target,iterations):
    if type(columns) is not list or not 2<=len(columns)<=80:raise ValueError('2..80 columns before scan')
    def num(v):
        if type(v) not in (int,float) or not -1000<=v<=1000 or not math.isfinite(v):raise ValueError('strict finite column number -1000..1000')
        return F(str(v))
    data=[]
    for row in columns:
        if type(row) is not list or len(row)!=2:raise ValueError('column coordinate and cost pair')
        data.append(tuple(map(num,row)))
    t=num(target)
    low=min(range(len(data)),key=lambda i:(data[i][0],i));high=max(range(len(data)),key=lambda i:(data[i][0],-i))
    if not data[low][0]<data[high][0] or not data[low][0]<=t<=data[high][0]:raise ValueError('target in nondegenerate column coordinate hull')
    if type(iterations) is not int or not 1<=iterations<=80:raise ValueError('strict column iterations 1..80')
    active=[low,high];trace=[];converged=False
    for _ in range(iterations):
        dual=[]
        for i,j in combinations(active,2):
            q,c=data[i];r,d=data[j]
            if q==r:continue
            beta=(d-c)/(r-q);alpha=c-beta*q
            if all(alpha+beta*data[k][0]<=data[k][1] for k in active):dual.append((alpha+beta*t,alpha,beta))
        value,alpha,beta=max(dual,key=lambda v:(v[0],v[1],v[2]))
        tight=[i for i in active if data[i][1]==alpha+beta*data[i][0]];mixtures=[]
        for i in tight:
            if data[i][0]==t:mixtures.append(((i,),[F(1)]))
        for i,j in combinations(tight,2):
            q=data[i][0];r=data[j][0]
            if q!=r and min(q,r)<=t<=max(q,r):
                w=(r-t)/(r-q);mixtures.append(((i,j),[w,1-w]))
        basis,weights=min(mixtures,key=lambda v:v[0]);pricing=[c-alpha-beta*q for q,c in data];enter=min(range(len(data)),key=lambda i:(pricing[i],i));reduced=pricing[enter]
        trace.append({'active_column_indices':active[:],'basis_indices':list(basis),'weights_fraction':[str(v) for v in weights],'restricted_objective_fraction':str(value),
                      'dual_intercept_fraction':str(alpha),'dual_slope_fraction':str(beta),'pricing_column_index':enter,'reduced_cost_fraction':str(reduced)})
        if reduced>=0:converged=True;break
        active.append(enter)
    return {'basis_indices':list(basis),'weights_fraction':[str(v) for v in weights],'objective_fraction':str(value),
            'converged_exact_in_supplied_menu':converged,'trace':trace,'iterations_used':len(trace),'external_effects':[]}
