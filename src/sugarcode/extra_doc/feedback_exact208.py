"""Exact rational synchronous linear stock feedback dynamics.
NOT_CLAIMED: authentic physical feedback model; stability for arbitrary matrices;
continuous ODE solution; real-world control; runtime integration.
"""
from fractions import Fraction
import math


def simulate(initial,matrix,forcing,dt,steps):
    if type(steps) is not int or not 0<=steps<=30:raise ValueError('strict feedback steps 0..30')
    if type(initial) is not list or not 1<=len(initial)<=8:raise ValueError('1..8 stocks before scan')
    n=len(initial)
    def number(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded feedback number')
        return Fraction(str(v))
    def vector(v):
        if type(v) is not list or len(v)!=n:raise ValueError('one feedback value per stock')
        return [number(q,-100,100) for q in v]
    x=vector(initial);u=vector(forcing);h=number(dt,.000001,1)
    if type(matrix) is not list or len(matrix)!=n:raise ValueError('square feedback matrix dimension')
    a=[vector(row) for row in matrix]
    trace=[{'step':0,'time_fraction':'0','stocks_fraction':[str(q) for q in x],'rates_fraction':[]}]
    for t in range(1,steps+1):
        rates=[sum(q*v for q,v in zip(row,x))+f for row,f in zip(a,u)]
        x=[v+h*q for v,q in zip(x,rates)]
        trace.append({'step':t,'time_fraction':str(t*h),'stocks_fraction':[str(q) for q in x],'rates_fraction':[str(q) for q in rates]})
    loops=[]
    # Enumerate each simple directed cycle once, anchored at its smallest index.
    def walk(path):
        start=path[0];current=path[-1]
        if a[start][current]!=0:
            coeff=Fraction(1)
            for left,right in zip(path,path[1:]+[start]):coeff*=a[right][left]
            loops.append({'stocks':path[:],'gain_fraction':str(coeff),'kind':'reinforcing' if coeff>0 else 'balancing'})
        if len(path)==n:return
        for nxt in range(start+1,n):
            if nxt not in path and a[nxt][current]!=0:walk(path+[nxt])
    for start in range(n):walk([start])
    return {'trace':trace,'final_stocks_fraction':[str(q) for q in x],'feedback_loops':loops,
            'method':'exact synchronous forward Euler linear feedback recurrence','units':'matrix inverse time; forcing stock per time; dt time',
            'stability_verified':False,'external_effects':[]}
