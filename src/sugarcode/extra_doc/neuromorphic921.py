"""Neuromorphic Computing - Brain-inspired hardware.

Bounded: deterministic software simulation of a synchronous digital leaky
integrate-and-fire array with recurrent delayed spikes. No fabricated hardware,
energy-efficiency claim, biological fidelity or autonomous learning.
"""
from math import isfinite


def simulate_array(currents, weights, leak=0.9, threshold=1.0, reset=0.0):
    """Run simultaneous discrete-time LIF updates with one-tick recurrent delay.

    weights[post][pre], no within-tick cascade. v'=leak*v+external+W*last_spikes;
    v'>=threshold emits and hard-resets. Initial potentials and spikes zero.
    1..64 cells, 1..1000 ticks. Input scalars finite built-in real magnitude <=100;
    leak in [0,1], threshold in (0,100], reset<threshold. Returns complete traces.
    """
    def real(x):
        if type(x) not in (int,float) or abs(x)>100 or not isfinite(x):
            raise ValueError('finite built-in real magnitude <=100 required')
    for x in (leak,threshold,reset):real(x)
    if not 0<=leak<=1 or not 0<threshold<=100 or not reset<threshold:
        raise ValueError('invalid leak, threshold or reset')
    if type(weights) not in (list,tuple) or not 1<=len(weights)<=64:
        raise ValueError('weights must be a square matrix with 1..64 cells')
    cells=len(weights)
    for row in weights:
        if type(row) not in (list,tuple) or len(row)!=cells:
            raise ValueError('weights must be a square matrix with 1..64 cells')
        for x in row:real(x)
    if type(currents) not in (list,tuple) or not 1<=len(currents)<=1000:
        raise ValueError('currents must contain 1..1000 ticks')
    for row in currents:
        if type(row) not in (list,tuple) or len(row)!=cells:
            raise ValueError('each current tick must match cell count')
        for x in row:real(x)
    v=[0.0]*cells;previous=[0]*cells;potentials=[];spikes=[]
    for current in currents:
        integrated=[leak*v[i]+current[i]+sum(weights[i][j]*previous[j] for j in range(cells)) for i in range(cells)]
        fired=[int(x>=threshold) for x in integrated]
        v=[reset if fired[i] else integrated[i] for i in range(cells)]
        previous=fired
        potentials.append(tuple(v));spikes.append(tuple(fired))
    return {'potentials':tuple(potentials),'spikes':tuple(spikes),
            'spike_counts':tuple(sum(row[i] for row in spikes) for i in range(cells)),
            'scope':'software synchronous discrete LIF array; no hardware'}
