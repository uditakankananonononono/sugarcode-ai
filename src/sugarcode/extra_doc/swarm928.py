"""Swarm Intelligence - Collective behavior algorithms.

PARTIAL: exact-rational synchronous two-dimensional separation/alignment/cohesion
swarm update with L1 speed clipping. No physical agents, learning, collision-
avoidance proof or global optimum guarantee. Caller-supplied state only.
"""
from fractions import Fraction
from math import isfinite

SCOPE='synchronous rational 2D separation alignment cohesion step; no physical swarm'


def step_swarm(rows,radius=1.0,separation=1.0,alignment=1.0,cohesion=1.0,max_speed=1.0):
    """Rows(id,x,y,vx,vy), exact list/tuple mixtures,1..32 unique labeled agents.

    Positions/velocities[-100,100], weights[0,10], radius(0,100], maxspeed(0,100].
    Neighbors include Euclidean distance<=radius, exclude self. Separation mean
    (self-pos -neighbor-pos)/distance^2, ignoring coincident pairs. Alignment
    mean neighbor velocity minus own; cohesion mean neighbor position minus own.
    v'=v+weighted forces; clip via L1 norm, then pos'=pos+v'. All simultaneous.
    Returns label-sorted output and neighbor sets. Fractions over decimal inputs.
    """
    def real(x,low,high):
        if type(x) not in (int,float) or not low<=x<=high or not isfinite(x):
            raise ValueError('finite built-in swarm real outside range')
        return Fraction(str(x))
    r=real(radius,0,100);s=real(separation,0,10);a=real(alignment,0,10);c=real(cohesion,0,10);speed=real(max_speed,0,100)
    if r==0 or speed==0:raise ValueError('radius and max_speed must be positive')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=32:
        raise ValueError('rows must contain1..32 agents')
    parsed={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=5:raise ValueError('agent must be list/tuple five-item row')
        label,*values=row
        if type(label) is not str or not 1<=len(label)<=24 or not label.isascii() or not all(ch.isalnum() or ch=='_' for ch in label):
            raise ValueError('exact ASCII alphanumeric/underscore label length1..24 required')
        if label in parsed:raise ValueError('agent labels must be unique')
        parsed[label]=tuple(real(x,-100,100) for x in values)
    output=[];neighbors=[]
    for label in sorted(parsed):
        x,y,vx,vy=parsed[label]
        close=[key for key,(xx,yy,_,_) in parsed.items() if key!=label and (x-xx)**2+(y-yy)**2<=r*r]
        forces=[Fraction(0)]*6
        for key in close:
            xx,yy,ux,uy=parsed[key];d=(x-xx)**2+(y-yy)**2
            if d:forces[0]+=(x-xx)/d;forces[1]+=(y-yy)/d
            forces[2]+=ux-vx;forces[3]+=uy-vy;forces[4]+=xx-x;forces[5]+=yy-y
        if close:
            vx+=sum(weight*forces[i] for weight,i in ((s,0),(a,2),(c,4)))/len(close)
            vy+=sum(weight*forces[i] for weight,i in ((s,1),(a,3),(c,5)))/len(close)
        norm=abs(vx)+abs(vy)
        if norm>speed:vx*=speed/norm;vy*=speed/norm
        output.append((label,x+vx,y+vy,vx,vy));neighbors.append((label,tuple(sorted(close))))
    return {'agents':tuple(output),'neighbors':tuple(neighbors),'scope':SCOPE}
