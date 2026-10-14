"""Exact ant-colony Hamiltonian-tour construction and pheromone update.
NOT_CLAIMED: optimal routing at finite budget; authentic cost data; random draw
provenance; real journey execution; runtime integration.
"""
from fractions import Fraction
import math


def generation(costs,pheromone,starts,draws,evaporation,deposit):
    if type(costs) is not list or not 2<=len(costs)<=8:raise ValueError('2..8 routing nodes before scan')
    n=len(costs)
    def num(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded ant number')
        return Fraction(str(v))
    def matrix(raw,lo,hi):
        if type(raw) is not list or len(raw)!=n:raise ValueError('square ant matrix dimensions')
        out=[]
        for row in raw:
            if type(row) is not list or len(row)!=n:raise ValueError('square ant matrix dimensions')
            out.append([num(v,lo,hi) for v in row])
        return out
    c=matrix(costs,0,1000);p=matrix(pheromone,.000001,1000)
    if any(c[i][i]!=0 or any(c[i][j]<=0 for j in range(n) if i!=j) for i in range(n)):raise ValueError('zero diagonal and positive offdiagonal routing costs')
    if type(starts) is not list or not 1<=len(starts)<=20:raise ValueError('1..20 ants before scan')
    if any(type(v) is not int or not 0<=v<n for v in starts):raise ValueError('strict ant start node indices')
    if type(draws) is not list or len(draws)!=len(starts):raise ValueError('one draw row per ant')
    ds=[]
    for row in draws:
        if type(row) is not list or len(row)!=n-1:raise ValueError('n-1 draws per ant')
        vals=[num(v,0,1) for v in row]
        if any(v==1 for v in vals):raise ValueError('ant draw strictly below one')
        ds.append(vals)
    rho=num(evaporation,0,1);q=num(deposit,0,1000);tours=[];increments=[[Fraction(0) for _ in range(n)] for _ in range(n)]
    for ant,(start,row) in enumerate(zip(starts,ds)):
        route=[start];remaining=set(range(n))-{start}
        for draw in row:
            current=route[-1];menu=sorted(remaining);weights=[p[current][j]/c[current][j] for j in menu];threshold=draw*sum(weights);running=Fraction(0);chosen=menu[-1]
            for node,weight in zip(menu,weights):
                running+=weight
                if threshold<running:chosen=node;break
            route.append(chosen);remaining.remove(chosen)
        route.append(start);length=sum(c[a][b] for a,b in zip(route,route[1:]));gain=q/length
        for a,b in zip(route,route[1:]):increments[a][b]+=gain
        tours.append({'ant':ant,'route':route,'cost_fraction':str(length)})
    updated=[[(1-rho)*p[i][j]+increments[i][j] for j in range(n)] for i in range(n)]
    best=min(tours,key=lambda t:(Fraction(t['cost_fraction']),t['ant']))
    return {'tours':tours,'best_ant':best['ant'],'best_route':best['route'],'best_cost_fraction':best['cost_fraction'],
            'pheromone_fraction':[[str(v) for v in row] for row in updated],'transition_rule':'pheromone / edge cost; strict cumulative draw threshold; ascending node order',
            'update_rule':'synchronous evaporation plus deposit/cost on each traversed directed edge','global_optimum_claimed':False,'external_effects':[]}
