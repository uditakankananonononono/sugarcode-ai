import pytest
from sugarcode.extra_doc.character_development import develop_character as solve


def test_compatible_persona_and_event_driven_multidimensional_arc():
    dims={'loyalty':['family','city'],'fear':['abandonment','failure'],'goal':['escape']}
    rule=('loyalty','family','fear','abandonment')
    r=solve(dims,[rule],[('betrayal','loyalty','family','city','protect others'),
                         ('reassurance','fear','failure','abandonment','trust partner'),
                         ('irrelevant','goal','stay','return','remember home')])
    # First tuple conflicts; second is family/failure/escape.
    assert r['persona']=={'loyalty':'family','fear':'failure','goal':'escape'}
    assert r['final_persona']=={'loyalty':'city','fear':'abandonment','goal':'escape'}
    assert [e['applied'] for e in r['arc']]==[True,True,False]
    assert r['arc'][0]['before']=='family' and r['arc'][0]['after']=='city'
    assert not any(e['contradictions'] for e in r['arc'])
    assert dims['loyalty']==['family','city'] and not r['creative_quality_claimed']


def test_new_internal_conflict_explicit_not_suppressed():
    rule=('value','mercy','goal','revenge')
    r=solve({'value':['justice','mercy'],'goal':['revenge']},[rule],
            [('loss','value','justice','mercy','forgive')])
    assert r['arc'][0]['contradictions']==[rule]
    assert r['arc'][0]['motivation']=='forgive'


def test_all_incompatible_and_shape_cap_precedes_contents():
    with pytest.raises(ValueError,match='^no compatible persona exists$'):
        solve({'a':['x'],'b':['y']},[('a','x','b','y')],[])
    with pytest.raises(ValueError,match='^dimension count must be between 2 and 6$'):
        solve({str(i):[None] for i in range(7)},[],[])
    assert len(solve({str(i):['a','b','c','d'] for i in range(6)},[],[])['persona'])==6

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[]),TypeError,'dimensions must be a dict'),
 (({'a':['x'],'b':['y']},None,[]),TypeError,'rules and events must be lists or tuples'),
 (({'a':['x'],'b':['y']},[None]*65,[]),ValueError,'rule count must not exceed 64 and event count 32'),
 (({'a':[None]*5,'b':['y']},[],[]),ValueError,'each dimension must have between 1 and 4 options'),
 (({'a':[True],'b':['y']},[],[]),TypeError,'labels must be strings'),
 (({'a':['x'*81],'b':['y']},[],[]),ValueError,'label length must be between 1 and 80'),
 (({'a':[' '],'b':['y']},[],[]),ValueError,'labels must not be blank'),
 (({'a':['x','x'],'b':['y']},[],[]),ValueError,'dimension options must be unique'),
 (({'a':['x'],'b':['y']},[('a','x','a','x')],[]),ValueError,'forbidden pair must reference distinct known dimensions and options'),
 (({'a':['x'],'b':['y']},[],[('e','z','x','y','m')]),ValueError,'event must reference a known dimension'),
])
def test_exact_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message


def test_exact_label_dimension_rule_event_boundaries():
    label='x'*80
    dims={'a':[label],'b':['y']}
    assert solve(dims,[],[])['persona']=={'a':label,'b':'y'}
    rules=[('a',label,'b','z')]*64
    valid_dims={'a':[label],'b':['y','z']}
    events=[('e','a',label,label,'m')]*32
    r=solve(valid_dims,rules,events)
    assert r['persona']=={'a':label,'b':'y'} and len(r['arc'])==32
    assert all(t['applied'] for t in r['arc'])

@pytest.mark.parametrize('args,message',[
 (({'a':['x']},[],[]),'dimension count must be between 2 and 6'),
 (({'a':['x'],'b':['y']},[],[None]*33),'rule count must not exceed 64 and event count 32'),
 (({'a':[],'b':['y']},[],[]),'each dimension must have between 1 and 4 options'),
 (({'a':['x'],'b':['y']},[None],[]),'forbidden pairs must have four fields'),
 (({'a':['x'],'b':['y']},[('a','x','b')],[]),'forbidden pairs must have four fields'),
 (({'a':['x'],'b':['y']},[],[None]),'events must have five fields'),
 (({'a':['x'],'b':['y']},[],[('e','a','x','y')]),'events must have five fields'),
])
def test_remaining_shape_and_lower_boundary_errors(args,message):
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)==message
