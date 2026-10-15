"""Systems Science (canonical2009): PARTIAL caller scalar disturbance reachability.

Exactints gain-3..3,initial-4..4,bound0..3,horizon0..5. xnext=gain*x+w, each
w arbitraryinteger[-bound,bound]. Returnreachablemin/maxatallsteps,worstabsolute
terminalstate,andcountofDISTINCTterminalstates (not assumedintervalfullyfilled).
Intervalextremes propagatedsignaware;distinctstates bysetrecurrence. Noactual
systemsafety/stability/validation. Validategain,initial,bound,horizon inthatorder.
"""
SCOPE='PARTIAL: caller bounded integer-disturbance scalar reachability extremes and state counts'
NOT_CLAIMED=('real system safety','stability validation','measured dynamics')


def reach(gain,initial,bound,horizon):
    for name,v,lo,hi in (('gain',gain,-3,3),('initial',initial,-4,4),('bound',bound,0,3),('horizon',horizon,0,5)):
        if type(v) is not int or not lo<=v<=hi:raise ValueError(name+' exact int'+str(lo)+'..'+str(hi))
    low=high=initial;intervals=[(low,high)];states={initial}
    for t in range(horizon):
        a,b=gain*low,gain*high;low=min(a,b)-bound;high=max(a,b)+bound;intervals.append((low,high));states={gain*s+w for s in states for w in range(-bound,bound+1)}
    return {'intervals':intervals,'terminal_count':len(states),'worst_absolute':max(abs(low),abs(high)),'system_validated':False}
