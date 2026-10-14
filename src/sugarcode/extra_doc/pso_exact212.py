"""Exact synchronous PSO step for squared distance to a supplied target.

NOT_CLAIMED: authentic objective; random draw provenance; global optimum;
real-world execution; runtime integration. Caller supplies draw matrices. Position clipping
zeros velocity on clipped axes. Personal/global best snapshots are old-state.
"""
from fractions import Fraction
import math


def advance(positions,velocities,personal_best,bounds,target,inertia,cognitive,social,cognitive_draws,social_draws):
    if type(target) is not list or not 1<=len(target)<=8:raise ValueError('1..8 target dimensions before scan')
    d=len(target)
    def num(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded PSO number')
        return Fraction(str(v))
    t=[num(v,-1000,1000) for v in target];coeff=[num(v,0,2) for v in (inertia,cognitive,social)]
    if type(bounds) is not list or len(bounds)!=d:raise ValueError('one ordered bound pair per target dimension')
    lim=[]
    for pair in bounds:
        if type(pair) is not list or len(pair)!=2:raise ValueError('one ordered bound pair per target dimension')
        a,b=[num(v,-1000,1000) for v in pair]
        if a>=b:raise ValueError('strictly ordered PSO bounds')
        lim.append((a,b))
    if type(positions) is not list or not 1<=len(positions)<=20:raise ValueError('1..20 particles before scan')
    n=len(positions)
    def matrix(rows,lo,hi):
        if type(rows) is not list or len(rows)!=n:raise ValueError('aligned particle matrix dimensions')
        out=[]
        for row in rows:
            if type(row) is not list or len(row)!=d:raise ValueError('aligned particle matrix dimensions')
            out.append([num(v,lo,hi) for v in row])
        return out
    pos=matrix(positions,-1000,1000);vel=matrix(velocities,-1000,1000);best=matrix(personal_best,-1000,1000)
    cd=matrix(cognitive_draws,0,1);sd=matrix(social_draws,0,1)
    for rows in (pos,best):
        if any(not a<=v<=b for row in rows for v,(a,b) in zip(row,lim)):raise ValueError('current and personal points inside bounds')
    objective=lambda point:sum((v-q)**2 for v,q in zip(point,t))
    if any(objective(b)>objective(p) for b,p in zip(best,pos)):raise ValueError('personal best no worse than current point')
    gi=min(range(n),key=lambda i:(objective(best[i]),i));global_old=best[gi]
    newpos=[];newvel=[];newbest=[]
    for i in range(n):
        p=[];v=[]
        for j,(a,b) in enumerate(lim):
            velocity=coeff[0]*vel[i][j]+coeff[1]*cd[i][j]*(best[i][j]-pos[i][j])+coeff[2]*sd[i][j]*(global_old[j]-pos[i][j])
            raw=pos[i][j]+velocity;point=min(b,max(a,raw))
            p.append(point);v.append(velocity if a<=raw<=b else Fraction(0))
        newpos.append(p);newvel.append(v);newbest.append(p if objective(p)<objective(best[i]) else list(best[i]))
    ng=min(range(n),key=lambda i:(objective(newbest[i]),i));encode=lambda rows:[[str(v) for v in row] for row in rows]
    return {'positions_fraction':encode(newpos),'velocities_fraction':encode(newvel),'personal_best_fraction':encode(newbest),
            'old_global_best_index':gi,'new_global_best_index':ng,'global_best_fraction':[str(v) for v in newbest[ng]],
            'old_best_loss_fraction':str(objective(global_old)),'new_best_loss_fraction':str(objective(newbest[ng])),
            'units':'positions target units; velocities target units/step; squared-distance loss assumes comparable axis units',
            'global_optimum_verified':False,'draw_randomness_verified':False,'external_effects':[],
            'assumptions':['one synchronous squared-distance step with caller draw matrices','ties preserve personal point and lowest particle index',
                           'clipped coordinate velocity zeroed; exact boundary landing keeps velocity']}
