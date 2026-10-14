"""Row 342 Difficulty Balancing: exact finite challenge-curve fitting.

Chooses supplied integer difficulty levels per stage to minimize squared
error to targets, while requiring nondecreasing progression and a maximum
adjacent increase. Dynamic programming avoids exponential enumeration.
Caps 32 stages/eight levels each; ties use lexicographic difficulty sequence.
NOT_CLAIMED: actual player skill estimation, engagement or frustration models,
universal challenge quality, runtime adaptation or deployment.
"""


def balance_difficulty(options,targets,max_increase):
    if type(options) not in (list,tuple) or type(targets) not in (list,tuple):
        raise TypeError('options and targets must be lists or tuples')
    if not 1<=len(options)<=32:raise ValueError('stage count must be between 1 and 32')
    if len(targets)!=len(options):raise ValueError('target count must match stages')
    for levels in options:
        if type(levels) not in (list,tuple) or not 1<=len(levels)<=8:
            raise ValueError('each stage must have between 1 and 8 levels')
    if type(max_increase) is not int or not 0<=max_increase<=100:
        raise ValueError('max_increase must be a nonbool integer zero through 100')
    if any(type(v) is not int or not 0<=v<=100 for v in targets):
        raise ValueError('targets must be nonbool integers zero through 100')
    for levels in options:
        if any(type(v) is not int or not 0<=v<=100 for v in levels):
            raise ValueError('levels must be nonbool integers zero through 100')
        if len(set(levels))!=len(levels):raise ValueError('levels must be unique')
    states={v:((v-targets[0])**2,(v,)) for v in options[0]}
    for levels,target in zip(options[1:],targets[1:]):
        nxt={}
        for value in levels:
            choices=[(cost+(value-target)**2,path+(value,)) for prior,(cost,path) in states.items()
                     if 0<=value-prior<=max_increase]
            if choices:nxt[value]=min(choices)
        states=nxt
    if not states:raise ValueError('no nondecreasing curve satisfies increase cap')
    cost,path=min(states.values())
    return {'difficulty_levels':list(path),'squared_error':cost,'player_experience_validated':False}
