"""Exact finite-hypothesis Bayesian optimization with expected improvement.
NOT_CLAIMED: general continuous optimizer; true prior or noise model; real
objective execution; global optimum; runtime integration.
"""
from fractions import Fraction
import math


def suggest(candidates,hypotheses,observations,noise_scale,direction):
    if type(direction) is not str or direction not in ('min','max'):raise ValueError('direction min or max')
    if type(candidates) is not list or not 2<=len(candidates)<=20:raise ValueError('2..20 candidate ids before scan')
    if any(type(v) is not str or not 1<=len(v)<=80 for v in candidates) or len(set(candidates))!=len(candidates):raise ValueError('unique candidate ids 1..80')
    n=len(candidates)
    def num(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded Bayesian number')
        return Fraction(str(v))
    scale=num(noise_scale,.000001,1000)
    if type(hypotheses) is not list or not 1<=len(hypotheses)<=20:raise ValueError('1..20 function hypotheses before scan')
    funcs=[];ids=set();weights=[]
    for h in hypotheses:
        if type(h) is not dict or set(h)!={'id','prior','values'}:raise ValueError('exact hypothesis id/prior/values fields')
        ident=h['id'];raw=h['values']
        if type(ident) is not str or not 1<=len(ident)<=80 or ident in ids:raise ValueError('unique hypothesis ids 1..80')
        ids.add(ident)
        if type(raw) is not list or len(raw)!=n:raise ValueError('one hypothesis value per candidate')
        funcs.append((ident,[num(v,-1000,1000) for v in raw]));weights.append(num(h['prior'],0,1))
    if sum(weights)!=1:raise ValueError('hypothesis priors sum exactly one')
    if type(observations) is not list or not 1<=len(observations)<=20:raise ValueError('1..20 observations before scan')
    obs=[];seen=set()
    for row in observations:
        if type(row) is not dict or set(row)!={'candidate','value'}:raise ValueError('exact observation candidate/value fields')
        name=row['candidate']
        if type(name) is not str or name not in candidates:raise ValueError('observation candidate in menu')
        value=num(row['value'],-1000,1000);obs.append((candidates.index(name),value));seen.add(name)
    if len(seen)==n:raise ValueError('at least one unobserved candidate required')
    posterior_history=[]
    for index,value in obs:
        # Cauchy density's scale/pi common to all hypotheses cancels on normalization.
        unnormalized=[w/(scale*scale+(value-f[index])**2) for w,(ident,f) in zip(weights,funcs)]
        normalizer=sum(unnormalized);weights=[w/normalizer for w in unnormalized]
        posterior_history.append([str(w) for w in weights])
    incumbent=(min if direction=='min' else max)(v for index,v in obs);scores=[]
    for j,name in enumerate(candidates):
        if name in seen:continue
        values=[f[j] for ident,f in funcs];mean=sum(w*v for w,v in zip(weights,values))
        improvement=[max(incumbent-v if direction=='min' else v-incumbent,0) for v in values]
        ei=sum(w*v for w,v in zip(weights,improvement));variance=sum(w*(v-mean)**2 for w,v in zip(weights,values))
        scores.append({'candidate':name,'expected_improvement_fraction':str(ei),'posterior_mean_fraction':str(mean),'posterior_variance_fraction':str(variance)})
    chosen=min(scores,key=lambda s:(-Fraction(s['expected_improvement_fraction']),candidates.index(s['candidate'])))
    return {'selected_candidate':chosen['candidate'],'scores':scores,'posterior_fraction':{ident:str(w) for w,(ident,f) in zip(weights,funcs)},
            'posterior_history_fraction':posterior_history,'incumbent_observed_fraction':str(incumbent),'direction':direction,
            'likelihood':'Cauchy observation noise with supplied scale, independent observations','selection':'maximum expected latent improvement; supplied candidate order ties',
            'objective_executed':False,'global_optimum_claimed':False,'external_effects':[]}
