import copy
import pytest
from sugarcode.extra_doc.narrative_plan261 import construct


def args():
    return [[dict(id='a',role='setup',text='Mira finds a map.',requires=[],adds=['map'],removes=[],tension=1),dict(id='b',role='inciting',text='A rival steals it.',requires=['map'],adds=['rival'],removes=['map'],tension=3),dict(id='c',role='escalation',text='Mira follows the rival.',requires=['rival'],adds=['trail'],removes=[],tension=5),dict(id='d',role='climax',text='She wins the map back.',requires=['trail'],adds=['map'],removes=['rival'],tension=9),dict(id='e',role='resolution',text='She reaches home.',requires=['map'],adds=['home'],removes=[],tension=2)],[],'home']


def test_genuine_generated_causal_arc_prose_goal_and_no_mutation():
    a=args();before=copy.deepcopy(a);r=construct(*a)
    assert r['story']=='At first, Mira finds a map. Then, A rival steals it. As the pressure grows, Mira follows the rival. At the turning point, She wins the map back. Afterward, She reaches home.'
    assert [e['id'] for e in r['arc']]==['a','b','c','d','e'] and [e['role'] for e in r['arc']]==['setup','inciting','escalation','climax','resolution']
    assert [e['state_after'] for e in r['arc']]==[['map'],['rival'],['rival','trail'],['map','trail'],['home','map','trail']]
    assert r['structural_contrast_score']==15 and r['candidate_arc_count']==1 and r['goal_fact']=='home' and r['goal_achieved_in_supplied_model']
    assert r['status']=='generated_causal_five_beat_arc' and r['review_required'] and not r['compelling_verified'] and r['external_effects']==[] and a==before


def test_real_alternative_choice_ties_and_infeasible_causal_tension_closure():
    a=args();alternative=copy.deepcopy(a[0][3]);alternative['id']='D';alternative['tension']=10;a[0].append(alternative)
    r=construct(*a);assert r['arc'][3]['id']=='D' and r['candidate_arc_count']==2 and r['structural_contrast_score']==17
    a[0][-1]['tension']=9;assert construct(*a)['arc'][3]['id']=='D'
    for reason in ('requires','removes','tension','goal','role'):
        a=args()
        if reason=='requires':a[0][1]['requires']=['missing']
        elif reason=='removes':a[0][1]['removes']=['missing']
        elif reason=='tension':a[0][2]['tension']=3
        elif reason=='goal':a[2]='absent'
        else:a[0][4]['role']='setup'
        r=construct(*a);assert r==dict(status='no_causal_five_beat_arc',candidate_arc_count=0,arc=[],story='',compelling_verified=False,external_effects=[])


def test_150_independent_role_product_plan_oracles():
    from itertools import product
    from random import Random
    rng=Random(261)
    for _ in range(150):
        a=args();extras=[]
        for role in ('setup','climax','resolution'):
            e=copy.deepcopy(next(e for e in a[0] if e['role']==role));e['id']='extra'+role;e['tension']=rng.randrange(11);extras.append(e)
        a[0]+=extras;choices=[[e for e in a[0] if e['role']==role] for role in ('setup','inciting','escalation','climax','resolution')];plans=[]
        for events in product(*choices):
            values=[e['tension'] for e in events]
            if any(values[j]>=values[j+1] for j in range(3)) or values[4]>=values[3]:continue
            state=set(a[1]);allowed=True
            for e in events:
                if any(f not in state for f in e['requires']+e['removes']):allowed=False;break
                for f in e['removes']:state.remove(f)
                for f in e['adds']:state.add(f)
            if allowed and a[2] in state:plans.append((2*values[3]-values[0]-values[4],tuple(e['id'] for e in events)))
        r=construct(*a);assert r['candidate_arc_count']==len(plans)
        if plans:
            expected=sorted(plans,key=lambda p:(-p[0],p[1]))[0];assert r['structural_contrast_score']==expected[0] and tuple(e['id'] for e in r['arc'])==expected[1]
        else:assert r['arc']==[]


def test_caps_text_facts_tension_schema_every_refusal_stage():
    a=args();a[0][0]['text']='x'*120;a[1]=[str(i) for i in range(10)];a[0][0]['tension']=0;a[0][3]['tension']=100;construct(*a)
    for events in (None,(),[],[{}]*4,[{}]*9):
        a=args();a[0]=events
        with pytest.raises(ValueError,match='^5..8 story events before scan$'):construct(*a)
    for e in ({},None,[],dict(args()[0][0],extra=1)):
        a=args();a[0][0]=e
        with pytest.raises(ValueError,match='^exact story event fields$'):construct(*a)
    for role in (None,True,'unknown'):
        a=args();a[0][0]['role']=role
        with pytest.raises(ValueError,match='^known five-beat role$'):construct(*a)
    for v in (True,1.0,None,'1',-1,101,10**400):
        a=args();a[0][0]['tension']=v
        with pytest.raises(ValueError,match='^strict integer tension 0..100$'):construct(*a)
    for facts in (None,(),True,[str(i) for i in range(11)]):
        for key in ('initial','requires','adds','removes'):
            a=args()
            if key=='initial':a[1]=facts
            else:a[0][0][key]=facts
            with pytest.raises(ValueError,match='^0..10 story facts before scan$'):construct(*a)
    a=args();a[1]=['a','a']
    with pytest.raises(ValueError,match='^unique story facts$'):construct(*a)
    a=args();a[0][0]['removes']=['map']
    with pytest.raises(ValueError,match='^disjoint added and removed facts$'):construct(*a)
    a=args();a[0][1]['id']='a'
    with pytest.raises(ValueError,match='^unique story event ids$'):construct(*a)
    for v in ('',None,True,' x','x ','x'*121,'x\u202e','x\n'):
        for key in ('goal','id','text','fact'):
            a=args()
            if key=='goal':a[2]=v
            elif key=='fact':a[1]=[v]
            else:a[0][0][key]=v
            with pytest.raises(ValueError,match='^strict visible trimmed story text 1..120$'):construct(*a)


def test_selected_arc_lexicographic_ids_not_event_payload_and_resolution_equal_peak_refused():
    a=args();other=copy.deepcopy(a[0][3]);other['id']='z';other['text']='A different ending.';a[0].append(other)
    r=construct(*a);assert r['arc'][3]['id']=='d' and 'A different ending.' not in r['story']
    a=args();a[0][4]['tension']=9
    assert construct(*a)['status']=='no_causal_five_beat_arc'


def test_required_facts_not_just_added_effects_and_sort_by_id_before_payload():
    a=args();a[0][4]['requires']=['absent'];a[0][4]['adds']=[];a[2]='map'
    assert construct(*a)['status']=='no_causal_five_beat_arc'
    a=args();a[0][3]['text']='Zulu climax.';e=copy.deepcopy(a[0][3]);e['id']='z';e['text']='Alpha climax.';a[0].append(e)
    r=construct(*a);assert r['arc'][3]['id']=='d' and r['arc'][3]['text']=='Zulu climax.'
