"""Generate causal five-beat story arcs by exact finite event-plan search.
NOT_CLAIMED: compelling to every reader; prose originality; psychological
realism; authentic events; publication or runtime integration.
"""
from itertools import permutations
import unicodedata


def construct(events,initial,goal):
    def text(v):
        if type(v) is not str or not 1<=len(v)<=120 or v!=v.strip() or any(unicodedata.category(c).startswith('C') for c in v):raise ValueError('strict visible trimmed story text 1..120')
        return v
    def facts(v):
        if type(v) is not list or len(v)>10:raise ValueError('0..10 story facts before scan')
        vals=[text(s) for s in v]
        if len(set(vals))!=len(vals):raise ValueError('unique story facts')
        return set(vals)
    state=facts(initial);wanted=text(goal)
    if type(events) is not list or not 5<=len(events)<=8:raise ValueError('5..8 story events before scan')
    menu=[];ids=set();roles=['setup','inciting','escalation','climax','resolution']
    for e in events:
        if type(e) is not dict or set(e)!={'id','role','text','requires','adds','removes','tension'}:raise ValueError('exact story event fields')
        ident=text(e['id']);prose=text(e['text']);role=e['role'];t=e['tension']
        if ident in ids:raise ValueError('unique story event ids')
        ids.add(ident)
        if type(role) is not str or role not in roles:raise ValueError('known five-beat role')
        if type(t) is not int or not 0<=t<=100:raise ValueError('strict integer tension 0..100')
        require=facts(e['requires']);add=facts(e['adds']);remove=facts(e['removes'])
        if add & remove:raise ValueError('disjoint added and removed facts')
        menu.append((ident,role,prose,require,add,remove,t))
    feasible=[]
    for sequence in permutations(menu,5):
        if [e[1] for e in sequence]!=roles:continue
        tension=[e[6] for e in sequence]
        if not tension[0]<tension[1]<tension[2]<tension[3] or not tension[4]<tension[3]:continue
        current=state.copy();states=[];valid=True
        for e in sequence:
            if not e[3]<=current or not e[5]<=current:valid=False;break
            current=(current-e[5])|e[4];states.append(sorted(current))
        if not valid or wanted not in current:continue
        score=tension[3]-tension[0]+tension[3]-tension[4]
        feasible.append((score,tuple(e[0] for e in sequence),sequence,states))
    if not feasible:return {'status':'no_causal_five_beat_arc','candidate_arc_count':0,'arc':[],'story':'','compelling_verified':False,'external_effects':[]}
    score,ids,selected,states=min(feasible,key=lambda c:(-c[0],c[1]))
    lead=['At first,','Then,','As the pressure grows,','At the turning point,','Afterward,']
    arc=[{'id':e[0],'role':e[1],'text':e[2],'tension':e[6],'state_after':state} for e,state in zip(selected,states)]
    story=' '.join(prefix+' '+e[2] for prefix,e in zip(lead,selected))
    return {'status':'generated_causal_five_beat_arc','candidate_arc_count':len(feasible),'arc':arc,'story':story,
            'structural_contrast_score':score,'goal_fact':wanted,'goal_achieved_in_supplied_model':True,
            'compelling_verified':False,'review_required':True,'external_effects':[]}
