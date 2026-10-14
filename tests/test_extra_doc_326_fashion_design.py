import pytest
from sugarcode.extra_doc.fashion_design import clothing_concept as solve


def test_four_concept_budget_and_compatibility_oracle():
    components=[[('plain',1,1),('tailored',3,5)],[('short',1,1),('long',4,7)]]
    #material/score2/2,5/8,4/6,7/12;budget5 selectsplain/long.
    r=solve(components,5)
    assert r=={'option_indices':[0,1],'labels':['plain','long'],'style_score':8,
              'material_used':5,'feasible_count':3,'fit_validated':False}
    assert solve(components,5,[(0,0,1,1)])['labels']==['tailored','short']


def test_score_tie_lower_material_then_first_order_caps():
    assert solve([[('a',3,5),('b',2,5),('c',2,5)]],3)['labels']==['b']
    assert solve([[('x'*40,0,1000000)]*4]*6,1000000)['feasible_count']==4096
    assert solve([[('x',0,0)]],0)['material_used']==0
    with pytest.raises(ValueError,match='^no compatible clothing concept fits material budget$'):
        solve([[('x',1,1)]],0)

@pytest.mark.parametrize('args,error,message',[
 ((None,0),TypeError,'components and forbidden pairs must be lists or tuples'),
 (([],0),ValueError,'component count must be between 1 and 6'),
 (([None]*7,0),ValueError,'component count must be between 1 and 6'),
 (([[('x',0,0)]],0,[None]*65),ValueError,'forbidden pair count must not exceed 64'),
 (([[]],0),ValueError,'each component must have between 1 and 4 options'),
 (([[None]*5],0),ValueError,'each component must have between 1 and 4 options'),
 (([[None]],0),ValueError,'options must contain label material and style_score'),
 (([[('x',0,0)]],True),ValueError,'material_budget must be a nonbool integer zero through 1000000'),
 (([[('x',0,0)]],-1),ValueError,'material_budget must be a nonbool integer zero through 1000000'),
 (([[('x',0,0)]],1000001),ValueError,'material_budget must be a nonbool integer zero through 1000000'),
 (([[(True,0,0)]],0),TypeError,'option labels must be strings'),
 (([[('',0,0)]],0),ValueError,'label length must be between 1 and 40'),
 (([[('x'*41,0,0)]],0),ValueError,'label length must be between 1 and 40'),
 (([[(' ',0,0)]],0),ValueError,'labels must not be blank'),
 (([[('x',True,0)]],0),ValueError,'material and scores must be nonbool integers zero through 1000000'),
 (([[('x',0,1000001)]],0),ValueError,'material and scores must be nonbool integers zero through 1000000'),
 (([[('x',0,0)]],0,[None]),ValueError,'forbidden pairs must contain component option component option'),
 (([[('x',0,0)]],0,[(0,0,0,0)]),ValueError,'rule components must be distinct nonbool valid indices'),
 (([[('x',0,0)],[('y',0,0)]],0,[(0,True,1,0)]),ValueError,'rule options must be nonbool valid indices'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message
