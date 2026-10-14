import pytest
from sugarcode.extra_doc.worldbuilding import build_world as solve


def test_implication_exclusion_generates_first_coherent_world_and_count():
    domains={'magic':['present','absent'],'power':['mages','council'],'law':['free','licensed']}
    r=solve(domains,[('magic','present','power','mages'),('power','mages','law','licensed')],
            [('magic','absent','power','mages')])
    # present/mages/licensed; absent/council/free; absent/council/licensed.
    assert r['world']=={'magic':'present','power':'mages','law':'licensed'}
    assert r['coherent_world_count']==3 and r['candidate_count']==8
    assert r['implication_certificate']==[True,True] and r['exclusion_certificate']==[True]
    assert not r['creative_quality_claimed'] and domains['magic']==['present','absent']


def test_vacuous_implication_self_constraint_and_unsatisfiable_rules():
    assert solve({'a':['x','y']},[('a','x','a','y')],[])['world']=={'a':'y'}
    with pytest.raises(ValueError,match='^no coherent world exists$'):
        solve({'a':['x']},[],[('a','x','a','x')])
    r=solve({str(i):['a','b','c','d'] for i in range(6)},[],[])
    assert r['coherent_world_count']==4096 and r['candidate_count']==4096

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[]),TypeError,'domains must be a dict'),
 (({},[],[]),ValueError,'dimension count must be between 1 and 6'),
 (({str(i):[None] for i in range(7)},[],[]),ValueError,'dimension count must be between 1 and 6'),
 (({'a':['x']},None,[]),TypeError,'rule sets must be lists or tuples'),
 (({'a':['x']},[None]*65,[]),ValueError,'each rule set must not exceed 64 rules'),
 (({'a':[None]*5},[],[]),ValueError,'each domain must have between 1 and 4 values'),
 (({'a':['x']},[('a','x')],[]),ValueError,'rules must have four fields'),
 (({'a':[True]},[],[]),TypeError,'labels must be strings'),
 (({'a':['x','x']},[],[]),ValueError,'domain values must be unique'),
 (({'a':['x']},[('a','x','a','z')],[]),ValueError,'rules must reference known dimensions and values'),
])
def test_exact_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message
