"""Spiking Neural Networks - Event-based processing.

PARTIAL: event-driven exponential LIF neuron with exact-form between-event
leak and refractory handling. No trained general network or physical hardware.
"""
from math import exp,isfinite


def event_neuron(events,tau=10.0,threshold=1.0,reset=0.0,refractory=0.0):
    """Process grouped simultaneous events, then threshold once per timestamp.

    Events are (time,weight) exact tuples, sorted nondecreasing, 0..1000 events.
    Times [0,1e6], weights [-100,100], tau [1e-6,1e6], threshold (0,100],
    reset [-100,threshold), refractory [0,1e6]. Built-in finite reals only.
    During [spike_time,spike_time+refractory) events are ignored. At the boundary
    they are accepted; reset decays from the last spike time. v starts at zero.
    Returns spike times and post-event voltage at each distinct event time.
    """
    def real(x,low,high):
        if type(x) not in (int,float) or not low<=x<=high or not isfinite(x):
            raise ValueError('finite built-in real outside supported range')
    real(tau,1e-6,1e6);real(threshold,1e-300,100);real(reset,-100,100);real(refractory,0,1e6)
    if reset>=threshold:raise ValueError('reset must be below threshold')
    if type(events) not in (list,tuple) or len(events)>1000:
        raise ValueError('events must be a list/tuple of at most 1000 entries')
    grouped=[]
    for event in events:
        if type(event) is not tuple or len(event)!=2:
            raise ValueError('each event must be an exact pair tuple')
        t,w=event;real(t,0,1e6);real(w,-100,100)
        if grouped and t<grouped[-1][0]:raise ValueError('event times must be nondecreasing')
        if grouped and t==grouped[-1][0]:grouped[-1]=(t,grouped[-1][1]+w)
        else:grouped.append((t,w))
    voltage=0.0;last=0.0;blocked_until=-1.0;spikes=[];trace=[]
    for t,w in grouped:
        voltage*=exp(-(t-last)/tau)
        last=t
        if t>=blocked_until:
            voltage+=w
            if voltage>=threshold:
                spikes.append(t);voltage=reset;blocked_until=t+refractory
        trace.append((t,voltage))
    return {'spike_times':tuple(spikes),'trace':tuple(trace),
            'scope':'event-driven single LIF neuron; no learned network'}
