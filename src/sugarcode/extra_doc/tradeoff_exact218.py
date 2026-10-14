"""Exact supplied-option normalized multi-goal compromise.
NOT_CLAIMED: global optimization; authentic feasible menu; true preferences;
real-world execution; runtime integration.
"""
from fractions import Fraction
import math


def choose(options,directions,weights):
    if type(directions) is not list or not 1<=len(directions)<=8:raise ValueError('1..8 objective directions before scan')
    if any(type(x) is not str or x not in ('min','max') for x in directions):raise ValueError('objective direction min or max')
    d=len(directions)
    def number(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded objective/weight value')
        return Fraction(str(v))
    if type(weights) is not list or len(weights)!=d:raise ValueError('one objective weight per direction')
    w=[number(v,0,1000) for v in weights]
    if not sum(w):raise ValueError('positive total objective weight')
    w=[v/sum(w) for v in w]
    if type(options) is not list or not 1<=len(options)<=100:raise ValueError('1..100 supplied options before scan')
    labels=[];vectors=[];seen=set()
    for row in options:
        if type(row) is not dict or set(row)!={'id','values'}:raise ValueError('exact id/values fields')
        label=row['id']
        if type(label) is not str or not 1<=len(label)<=120 or not label.strip():raise ValueError('bounded nonblank option id')
        if label in seen:raise ValueError('distinct option ids')
        seen.add(label);labels.append(label);values=row['values']
        if type(values) is not list or len(values)!=d:raise ValueError('one option value per direction')
        vector=[number(v,-1000000,1000000) for v in values]
        vectors.append([v if direction=='min' else -v for v,direction in zip(vector,directions)])
    ideal=[min(v[j] for v in vectors) for j in range(d)]
    spans=[max(v[j] for v in vectors)-ideal[j] for j in range(d)]
    front=[i for i,v in enumerate(vectors) if not any(all(a<=b for a,b in zip(other,v)) and any(a<b for a,b in zip(other,v)) for other in vectors)]
    scored=[]
    for i in front:
        regret=[(vectors[i][j]-ideal[j])/spans[j] if spans[j] else Fraction(0) for j in range(d)]
        score=max(weight*r for weight,r in zip(w,regret))
        scored.append((score,labels[i],regret))
    scored.sort(key=lambda x:(x[0],x[1]))
    return {'selected_id':scored[0][1],'frontier_ids':sorted(labels[i] for i in front),
            'dominated_ids':sorted(labels[i] for i in range(len(labels)) if i not in front),
            'weights_fraction':[str(v) for v in w],
            'scores':[{'id':label,'max_weighted_regret_fraction':str(score),'normalized_regrets_fraction':[str(v) for v in regret]} for score,label,regret in scored],
            'directions':list(directions),'units':'dimensionless range-normalized regrets; input objective units may differ',
            'normalization':'ideal and range from all supplied options; constant objective regret zero',
            'global_optimum_verified':False,'preferences_truth_verified':False,'external_effects':[],
            'assumptions':['only supplied feasible options considered; feasibility/provenance unverified',
                           'weight preferences supplied; no preference inference',
                           'changing option menu changes normalization and may change compromise']}
