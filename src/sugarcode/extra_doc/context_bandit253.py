"""Exact context-stratified Bernoulli posterior policy with supplied history.
NOT_CLAIMED: arbitrary context generalization, authentic rewards, exploration
regret guarantees, actual arm execution or runtime integration.
"""
from fractions import Fraction as F


def choose(arms,history,context):
    if type(arms) is not list or not 1<=len(arms)<=20:raise ValueError('1..20 context arms before scan')
    def ident(v):
        if type(v) is not str or not 1<=len(v)<=80 or not v.strip():raise ValueError('nonblank context identifiers 1..80')
        return v
    names=[ident(v) for v in arms]
    if len(set(names))!=len(names):raise ValueError('unique context arms')
    ctx=ident(context)
    if type(history) is not list or len(history)>1000:raise ValueError('0..1000 context observations before scan')
    counts={a:[0,0] for a in names};matched=0;total={a:[0,0] for a in names}
    for row in history:
        if type(row) is not dict or set(row)!={'context','arm','reward'}:raise ValueError('exact context arm reward fields')
        c=ident(row['context']);a=ident(row['arm']);r=row['reward']
        if a not in counts:raise ValueError('known context arm')
        if type(r) is not int or r not in (0,1):raise ValueError('strict Bernoulli context reward 0 or 1')
        total[a][0]+=r;total[a][1]+=1-r
        if c==ctx:counts[a][0]+=r;counts[a][1]+=1-r;matched+=1
    scores=[]
    for a in names:
        success,failure=counts[a];mean=F(success+1,success+failure+2)
        scores.append({'arm':a,'context_successes':success,'context_failures':failure,'posterior_mean_fraction':str(mean),'all_context_count':sum(total[a])})
    best=max(range(len(scores)),key=lambda i:(F(scores[i]['posterior_mean_fraction']),-i))
    return {'selected_arm':names[best],'context':ctx,'scores':scores,'matched_observations':matched,'total_observations':len(history),
            'unseen_context_prior':'independent Beta(1,1) per arm','tie_break':'input arm order','external_effects':[]}
