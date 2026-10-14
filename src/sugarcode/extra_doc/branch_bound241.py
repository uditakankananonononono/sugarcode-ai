"""Exact binary knapsack branch-and-bound with fractional relaxation bounds.
NOT_CLAIMED: arbitrary integer programs; large-scale throughput; authentic
items or model; external execution or runtime integration.
"""
from fractions import Fraction as F
import math


def solve(weights,values,capacity):
    if type(weights) is not list or not 1<=len(weights)<=16:raise ValueError('1..16 knapsack items before scan')
    n=len(weights)
    def num(v,lo):
        if type(v) not in (int,float) or not lo<=v<=1000 or not math.isfinite(v):raise ValueError('strict finite bounded knapsack number')
        return F(str(v))
    w=[num(v,.000001) for v in weights]
    if type(values) is not list or len(values)!=n:raise ValueError('one value per knapsack item')
    v=[num(z,0) for z in values];cap=num(capacity,0)
    order=sorted(range(n),key=lambda i:(-v[i]/w[i],i));best=F(0);bits=(0,)*n;visited=0;pruned=0;trace=[]
    def bound(k,remaining,value):
        result=value
        for i in order[k:]:
            take=min(remaining,w[i]);result+=take*v[i]/w[i];remaining-=take
            if remaining==0:break
        return result
    stack=[(0,cap,F(0),(0,)*n)]
    while stack:
        k,remaining,value,chosen=stack.pop();visited+=1;upper=bound(k,remaining,value)
        if upper<best:
            pruned+=1;trace.append({'depth':k,'upper_bound_fraction':str(upper),'incumbent_fraction':str(best)});continue
        if k==n:
            if value>best or (value==best and chosen<bits):best=value;bits=chosen
            continue
        i=order[k];stack.append((k+1,remaining,value,chosen))
        if w[i]<=remaining:
            included=list(chosen);included[i]=1;stack.append((k+1,remaining-w[i],value+v[i],tuple(included)))
    return {'selected_bits':list(bits),'value_fraction':str(best),'weight_fraction':str(sum(q*b for q,b in zip(w,bits))),
            'item_order':order,'nodes_visited':visited,'nodes_pruned_by_bound':pruned,'pruning_trace':trace,
            'optimal_in_supplied_binary_knapsack':True,'tie_break':'lexicographically smallest original-order bit vector','external_effects':[]}
