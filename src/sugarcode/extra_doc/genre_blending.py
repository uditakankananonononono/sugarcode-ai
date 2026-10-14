"""Row270 Genre Blending: exact compatible convention-outline generation.

Choose one supplied weighted convention per genre, maximize total supplied
weight under explicit pair incompatibilities, realize ordered genre beats.
Certificate reports covered genres, score and violated pairs for infeasibility
(best unconstrained outline witness). NOT_CLAIMED artistic innovation, narrative
quality, learned genre knowledge, original prose or unbounded creative ability.
"""
from itertools import product


def genre_blending(genres,conflicts):
    if not isinstance(genres,list) or not 2<=len(genres)<=4:raise ValueError('genre cap 2..4 required')
    if not isinstance(conflicts,list) or len(conflicts)>10:raise ValueError('conflict cap 0..10 required')
    names=set()
    for genre in genres:
        if not isinstance(genre,list) or not 1<=len(genre)<=3:raise ValueError('convention cap 1..3 required')
        local=set()
        for item in genre:
            if type(item) is not tuple or len(item)!=2:raise ValueError('name/weight pair required')
            name,weight=item
            if type(name) is not str or not 1<=len(name)<=20:raise ValueError('bounded convention name required')
            if type(weight) is not int:raise TypeError('nonbool exact weight required')
            if not 0<=weight<=10:raise ValueError('weight range 0..10 required')
            if name in local:raise ValueError('duplicate convention within genre')
            local.add(name);names.add(name)
    for pair in conflicts:
        if type(pair) is not tuple or len(pair)!=2:raise ValueError('conflict pair required')
        if any(type(x) is not str or len(x)>20 for x in pair):raise ValueError('bounded conflict names required')
        if pair[0]==pair[1] or any(x not in names for x in pair):raise ValueError('distinct known conflict names required')
    best=None;witness=None
    for indices in product(*(range(len(g)) for g in genres)):
        words=tuple(genres[i][j][0] for i,j in enumerate(indices))
        score=sum(genres[i][j][1] for i,j in enumerate(indices))
        violated=[pair for pair in conflicts if pair[0] in words and pair[1] in words]
        candidate=(-score,indices,words)
        if witness is None or candidate<witness[0]:witness=(candidate,violated)
        if not violated and (best is None or candidate<best):best=candidate
    if best is None:
        return {'conventions':None,'indices':None,'outline':None,
                'certificate':{'score':None,'conflicts':witness[1],'all_genres_covered':False,'optimal':False}}
    score,indices,words=best
    return {'conventions':list(words),'indices':list(indices),'outline':list(enumerate(words)),
            'certificate':{'score':-score,'conflicts':[],'all_genres_covered':True,'optimal':True}}
