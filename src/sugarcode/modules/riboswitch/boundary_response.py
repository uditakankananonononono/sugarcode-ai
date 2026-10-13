"""Bounded explicit-import response alternative for core.py:105-111.

Legacy accepts nonfinite/bool values, overflows power ratios, and divides
by zero when basal=0. This supplied-parameter Hill model is not performance.
"""
import math


def _number(v,name,cap=1e100):
    if isinstance(v,bool):raise ValueError(name+' must not be bool')
    if not isinstance(v,(int,float)):raise ValueError(name+' must be numeric')
    if abs(v)>cap:raise ValueError(name+' exceeds cap')
    if not math.isfinite(v):raise ValueError(name+' must be finite')
    return float(v)


def response_curve(kd_uM,*,mode='on',hill=1.5,basal=.05,maximum=1,concentrations=None):
    kd=_number(kd_uM,'kd');h=_number(hill,'hill',100)
    b=_number(basal,'basal');m=_number(maximum,'maximum')
    if kd<1e-100 or h<=0 or not 0<=b<m:raise ValueError('positive kd/hill and 0<=basal<maximum required')
    if mode not in ('on','off'):raise ValueError('mode must be on/off')
    if concentrations is None:concentrations=[kd*10**(-3+i/10) for i in range(61)]
    if not isinstance(concentrations,(list,tuple)) or not 2<=len(concentrations)<=10000:
        raise ValueError('bounded 2..10000 point list required')
    c=[_number(x,'concentration',1e103) for x in concentrations]
    if any(x<0 for x in c) or any(x>y for x,y in zip(c,c[1:])):raise ValueError('nonnegative sorted concentrations required')
    rows=[]
    for x in c:
        if not x:o=0.
        else:
            z=h*(math.log(x)-math.log(kd))
            e=math.exp(-abs(z));o=1/(1+e) if z>=0 else e/(1+e)
        rows.append({'concentration_uM':x,'occupancy':o,'signal':b+(m-b)*(o if mode=='on' else 1-o)})
    return {'curve':rows,'dynamic_range':m/b if b else None,
            'mode':mode,'kd_uM':kd,'ec50_uM':kd,'hill_coefficient':h,'basal':b,'maximum':m,
            'model_status':'PARTIAL supplied-parameter equilibrium model; no sensor performance claim'}
