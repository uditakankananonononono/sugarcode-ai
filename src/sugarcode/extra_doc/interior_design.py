"""Row 323 Interior Design: exact finite functional rectangle floor plan.

Selects one supplied placement (x,y,width,height,cost) per furniture item,
inside an integer room, forbidding positive-area overlap. Edge contact is
allowed. Minimizes total supplied functional cost, first product-order tie.
At most six items/four options each/4096 candidate plans.
NOT_CLAIMED: building-code compliance, ergonomics validation, aesthetics,
accessibility, arbitrary CAD modeling, fabrication or deployment.
"""
from itertools import product


def plan_interior(room_width,room_height,placements):
    for dimension in (room_width,room_height):
        if type(dimension) is not int or not 1<=dimension<=1000:
            raise ValueError('room dimensions must be nonbool integers between 1 and 1000')
    if type(placements) not in (list,tuple):raise TypeError('placements must be a list or tuple')
    if not 1<=len(placements)<=6:raise ValueError('item count must be between 1 and 6')
    for options in placements:
        if type(options) not in (list,tuple) or not 1<=len(options)<=4:
            raise ValueError('each item must have between 1 and 4 placements')
    for options in placements:
        for p in options:
            if type(p) not in (list,tuple) or len(p)!=5:
                raise ValueError('placements must contain x y width height cost')
    for options in placements:
        for x,y,w,h,cost in options:
            if any(type(v) is not int for v in (x,y,w,h,cost)):
                raise TypeError('placement fields must be nonbool integers')
            if not 0<=x<room_width or not 0<=y<room_height or not 1<=w<=room_width or not 1<=h<=room_height:
                raise ValueError('placement geometry must be inside room bounds')
            if x+w>room_width or y+h>room_height:raise ValueError('placement geometry must be inside room bounds')
            if not 0<=cost<=1000000:raise ValueError('costs must be between zero and 1000000')
    best=None;feasible=0;candidates=0
    for indices in product(*(range(len(options)) for options in placements)):
        candidates+=1;plan=[placements[i][j] for i,j in enumerate(indices)]
        overlap=False
        for i in range(len(plan)):
            for j in range(i+1,len(plan)):
                x,y,w,h,c=plan[i];a,b,u,v,d=plan[j]
                if x<a+u and a<x+w and y<b+v and b<y+h:overlap=True
        if overlap:continue
        feasible+=1;cost=sum(p[4] for p in plan)
        if best is None or cost<best[0]:best=(cost,indices,plan)
    if best is None:raise ValueError('no nonoverlapping interior plan exists')
    cost,indices,plan=best
    return {'placement_indices':list(indices),'rectangles':[list(p[:4]) for p in plan],
            'functional_cost':cost,'candidate_count':candidates,'feasible_count':feasible,'building_compliance_validated':False}
