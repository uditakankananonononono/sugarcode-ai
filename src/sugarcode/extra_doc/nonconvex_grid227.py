"""Exact multistart descent on supplied finite quartic grid landscapes.
NOT_CLAIMED: global continuous optimum; escape from every basin; authentic
objective; scalable optimization; runtime integration or external execution.
"""
from fractions import Fraction
import math


def explore(axes,linear,coupling,starts,max_steps):
    if type(axes) is not list or not 1<=len(axes)<=4:raise ValueError('1..4 landscape axes before scan')
    n=len(axes);count=1
    for axis in axes:
        if type(axis) is not list or not 1<=len(axis)<=7:raise ValueError('1..7 grid values per axis before scan')
        count*=len(axis)
    if count>2401:raise ValueError('at most 2401 grid vertices before expansion')
    def num(v):
        if type(v) not in (int,float) or not -10<=v<=10 or not math.isfinite(v):raise ValueError('strict finite landscape number -10..10')
        return Fraction(str(v))
    grid=[]
    for axis in axes:
        row=[num(v) for v in axis]
        if any(a>=b for a,b in zip(row,row[1:])):raise ValueError('strict ascending grid values')
        grid.append(row)
    if type(linear) is not list or len(linear)!=n:raise ValueError('one linear coefficient per axis')
    b=[num(v) for v in linear];c=num(coupling)
    if type(starts) is not list or not 1<=len(starts)<=20:raise ValueError('1..20 starts before scan')
    indices=[]
    for start in starts:
        if type(start) is not list or len(start)!=n:raise ValueError('one strict grid index per axis')
        if any(type(v) is not int or not 0<=v<len(grid[i]) for i,v in enumerate(start)):raise ValueError('strict grid index in axis bounds')
        indices.append(tuple(start))
    if type(max_steps) is not int or not 1<=max_steps<=100:raise ValueError('strict landscape budget 1..100')
    def value(idx):
        x=[grid[i][v] for i,v in enumerate(idx)]
        return sum((v*v-1)**2+b[i]*v for i,v in enumerate(x))+c*sum(x[i]*x[i+1] for i in range(n-1))
    runs=[]
    for start in indices:
        current=start;trace=[start];values=[value(start)];local=False
        for _ in range(max_steps):
            neighbors=[]
            for i in range(n):
                for delta in (-1,1):
                    j=current[i]+delta
                    if 0<=j<len(grid[i]):
                        v=list(current);v[i]=j;neighbors.append(tuple(v))
            best=min(neighbors,key=lambda p:(value(p),p)) if neighbors else current
            if value(best)>=values[-1]:local=True;break
            current=best;trace.append(current);values.append(value(current))
        runs.append({'indices':list(current),'point_fraction':[str(grid[i][v]) for i,v in enumerate(current)],'objective_fraction':str(values[-1]),
                     'index_trace':[list(v) for v in trace],'objective_trace_fraction':[str(v) for v in values],'local_minimum_observed':local,'moves_used':len(trace)-1})
    winner=min(range(len(runs)),key=lambda i:(Fraction(runs[i]['objective_fraction']),tuple(runs[i]['indices']),i))
    return {'runs':runs,'winner_index':winner,'grid_vertex_count':count,'global_grid_optimum_claimed':False,'global_continuous_optimum_claimed':False,'external_effects':[]}
