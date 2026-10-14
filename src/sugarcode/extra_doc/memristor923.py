"""Memristor Computing - In-memory processing.

PARTIAL: exact-rational passive crossbar matrix-vector multiplication and
bounded linear conductance programming model. Not fabricated memristors,
measured device behavior, sneak-path simulation or energy-efficiency evidence.
"""
from fractions import Fraction
from math import isfinite

SCOPE='ideal passive crossbar and clipped linear conductance model; no hardware'


def _number(x,low,high):
    if type(x) not in (int,float) or not low<=x<=high or not isfinite(x):
        raise ValueError('finite built-in crossbar real outside supported range')
    return Fraction(str(x))


def crossbar(conductances,voltages,pulses=None,gain=0.01,minimum=0.0,maximum=1.0):
    """Return read currents before/after simultaneous conductance programming.

    Matrix rows are output wires; columns are input wires. I=G*V exactly over
    decimal rational inputs. 1..32 rows/columns, G in[minimum,maximum], voltages
    [-10,10], programming pulses[-100,100]. G'=clip(G+gain*pulse,min,max).
    Programming uses the old matrix simultaneously. No circuit parasitics.
    Scalars finite exact built-in int/float only, not subclasses; row list/tuple
    mixtures accepted. Returns Fraction currents/conductances and power read
    power sum(G*V^2), before and after. No pulse-energy prediction.
    """
    lo=_number(minimum,0,100);hi=_number(maximum,0,100);step=_number(gain,0,1)
    if lo>=hi:raise ValueError('minimum must be below maximum')
    if type(conductances) not in (list,tuple) or not 1<=len(conductances)<=32:
        raise ValueError('conductances must have 1..32 output rows')
    if type(voltages) not in (list,tuple) or not 1<=len(voltages)<=32:
        raise ValueError('voltages must have 1..32 input entries')
    cols=len(voltages);volts=[_number(v,-10,10) for v in voltages]
    def matrix(raw,low,high,message):
        if type(raw) not in (list,tuple) or len(raw)!=len(conductances):
            raise ValueError(message)
        out=[]
        for row in raw:
            if type(row) not in (list,tuple) or len(row)!=cols:raise ValueError(message)
            out.append([_number(x,low,high) for x in row])
        return out
    g=matrix(conductances,lo,hi,'conductance rows must match input count')
    ps=[[Fraction(0)]*cols for _ in g] if pulses is None else matrix(pulses,-100,100,'pulse matrix must match conductances')
    updated=[[max(lo,min(hi,x+step*p)) for x,p in zip(row,pulse)] for row,pulse in zip(g,ps)]
    def read(rows):return tuple(sum(x*v for x,v in zip(row,volts)) for row in rows)
    def power(rows):return sum(x*v*v for row in rows for x,v in zip(row,volts))
    return {'currents_before':read(g),'currents_after':read(updated),
            'conductances_after':tuple(tuple(row) for row in updated),
            'power_before':power(g),'power_after':power(updated),'scope':SCOPE}
