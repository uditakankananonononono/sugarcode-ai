"""Exact synchronous DE/rand/1/bin generation on supplied squared-distance target."""
from fractions import Fraction
import math


def evolve(population,bounds,target,donors,draws,forced_coordinates,differential_weight,crossover_probability):
    if type(target) is not list or not 1<=len(target)<=8:raise ValueError('1..8 target dimensions before scan')
    d=len(target)
    def number(value,lower,upper):
        if type(value) not in (int,float) or not lower<=value<=upper or not math.isfinite(value):raise ValueError('strict finite bounded DE number')
        return Fraction(str(value))
    t=[number(v,-1000,1000) for v in target];f=number(differential_weight,0,2);cr=number(crossover_probability,0,1)
    if type(population) is not list or not 4<=len(population)<=20:raise ValueError('4..20 population points before scan')
    n=len(population)
    if type(bounds) is not list or len(bounds)!=d:raise ValueError('one ordered bound pair per dimension')
    lim=[]
    for pair in bounds:
        if type(pair) is not list or len(pair)!=2:raise ValueError('one ordered bound pair per dimension')
        a,b=[number(v,-1000,1000) for v in pair]
        if a>=b:raise ValueError('strictly ordered DE bounds')
        lim.append((a,b))
    def matrix(rows,lower,upper):
        if type(rows) is not list or len(rows)!=n:raise ValueError('aligned population matrix dimensions')
        result=[]
        for row in rows:
            if type(row) is not list or len(row)!=d:raise ValueError('aligned population matrix dimensions')
            result.append([number(v,lower,upper) for v in row])
        return result
    old=matrix(population,-1000,1000);random=matrix(draws,0,1)
    if any(not a<=v<=b for row in old for v,(a,b) in zip(row,lim)):raise ValueError('population inside bounds')
    if type(donors) is not list or len(donors)!=n:raise ValueError('three distinct nonself donor indices per point')
    for i,row in enumerate(donors):
        if type(row) is not list or len(row)!=3 or any(type(j) is not int or not 0<=j<n or j==i for j in row) or len(set(row))!=3:
            raise ValueError('three distinct nonself donor indices per point')
    if type(forced_coordinates) is not list or len(forced_coordinates)!=n or any(type(j) is not int or not 0<=j<d for j in forced_coordinates):
        raise ValueError('one strict forced coordinate per point')
    objective=lambda point:sum((v-q)**2 for v,q in zip(point,t))
    trials=[];next_population=[];accepted=[]
    for i,point in enumerate(old):
        a,b,c=[old[j] for j in donors[i]]
        mutant=[min(hi,max(lo,x+f*(y-z))) for x,y,z,(lo,hi) in zip(a,b,c,lim)]
        trial=[mutant[j] if random[i][j]<cr or j==forced_coordinates[i] else point[j] for j in range(d)]
        improved=objective(trial)<objective(point)
        trials.append(trial);next_population.append(trial if improved else list(point));accepted.append(improved)
    best=min(range(n),key=lambda i:(objective(next_population[i]),i));encode=lambda rows:[[str(v) for v in row] for row in rows]
    return {'trial_points_fraction':encode(trials),'population_fraction':encode(next_population),'accepted':accepted,
            'best_index':best,'best_point_fraction':[str(v) for v in next_population[best]],
            'best_loss_fraction':str(objective(next_population[best])),
            'units':'points in supplied target units; squared-distance loss assumes comparable axis units',
            'global_optimum_verified':False,'random_sampling_verified':False,'external_effects':[],
            'assumptions':['synchronous old-generation donors; caller draw/index matrices supplied',
                           'strict draw<CR; forced coordinate always crosses; exact CR0 still forces one',
                           'box clipping on mutant; strict improvement selection retains old point on ties']}
