"""Row 326 Fashion Design: finite compatible clothing-concept generation.

Chooses one supplied panel/material concept per garment component within a
material budget, avoiding forbidden component-option pairs, maximizing supplied
style scores. Equal scores prefer lower material, then supplied product order.
NOT_CLAIMED: original fashion taste, fit, sewing patterns, manufacturing,
physical garment simulation, trend validation or autonomous publication.
"""
from itertools import product


def clothing_concept(components,material_budget,forbidden_pairs=()):
    if type(components) not in (list,tuple) or type(forbidden_pairs) not in (list,tuple):
        raise TypeError('components and forbidden pairs must be lists or tuples')
    if not 1<=len(components)<=6:raise ValueError('component count must be between 1 and 6')
    if len(forbidden_pairs)>64:raise ValueError('forbidden pair count must not exceed 64')
    for options in components:
        if type(options) not in (list,tuple) or not 1<=len(options)<=4:
            raise ValueError('each component must have between 1 and 4 options')
    for options in components:
        for option in options:
            if type(option) not in (list,tuple) or len(option)!=3:
                raise ValueError('options must contain label material and style_score')
    if type(material_budget) is not int or not 0<=material_budget<=1000000:
        raise ValueError('material_budget must be a nonbool integer zero through 1000000')
    for options in components:
        for label,material,score in options:
            if type(label) is not str:raise TypeError('option labels must be strings')
            if not 1<=len(label)<=40:raise ValueError('label length must be between 1 and 40')
            if not label.strip():raise ValueError('labels must not be blank')
            if any(type(v) is not int or not 0<=v<=1000000 for v in (material,score)):
                raise ValueError('material and scores must be nonbool integers zero through 1000000')
    for rule in forbidden_pairs:
        if type(rule) not in (list,tuple) or len(rule)!=4:
            raise ValueError('forbidden pairs must contain component option component option')
        a,x,b,y=rule
        if type(a) is not int or type(b) is not int or not 0<=a<len(components) or not 0<=b<len(components) or a==b:
            raise ValueError('rule components must be distinct nonbool valid indices')
        if type(x) is not int or type(y) is not int or not 0<=x<len(components[a]) or not 0<=y<len(components[b]):
            raise ValueError('rule options must be nonbool valid indices')
    best=None;feasible=0
    for indices in product(*(range(len(options)) for options in components)):
        if any(indices[a]==x and indices[b]==y for a,x,b,y in forbidden_pairs):continue
        chosen=[components[i][j] for i,j in enumerate(indices)]
        material=sum(option[1] for option in chosen)
        if material>material_budget:continue
        feasible+=1;score=sum(option[2] for option in chosen)
        if best is None or score>best[0] or (score==best[0] and material<best[1]):
            best=(score,material,indices,chosen)
    if best is None:raise ValueError('no compatible clothing concept fits material budget')
    score,material,indices,chosen=best
    return {'option_indices':list(indices),'labels':[option[0] for option in chosen],
            'style_score':score,'material_used':material,'feasible_count':feasible,'fit_validated':False}
