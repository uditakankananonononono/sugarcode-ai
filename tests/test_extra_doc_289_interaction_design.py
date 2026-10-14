from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.interaction_design import plan_interaction as solve


def test_independent_simple_path_costs_choose_multistep_over_direct():
    edges=[('home','direct','done',7),('home','open','form',2),('form','submit','done',3),('form','back','home',0)]
    r=solve(['home','form','done','unused'],edges,'home','done')
    # Only simple goal paths: direct7 or open+submit5.
    assert r=={'transition_indices':[1,2],'actions':['open','submit'],'state_path':['home','form','done'],
              'total_effort':5,'reachable_states':['done','form','home'],'engagement_validated':False}


def test_zero_cycle_tie_order_fractional_and_identity():
    edges=[('a','first','b',0),('a','second','b',0),('b','back','a',0),('b','finish','c',F(1,2))]
    assert solve(['a','b','c'],edges,'a','c')['transition_indices']==[0,3]
    assert solve(['a'],[],'a','a')['state_path']==['a']
    with pytest.raises(ValueError,match='^goal is unreachable$'):solve(['a','b'],[],'a','b')
    for value in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        assert solve(['a','b'],[('a','go','b',value)],'a','b')['total_effort']==value
    assert len(solve([str(i) for i in range(32)],[], '0','0')['reachable_states'])==1
    assert solve(['a'],[('a','stay','a',0)]*128,'a','a')['total_effort']==0

@pytest.mark.parametrize('args,error,message',[
 ((None,[],'a','a'),TypeError,'states and transitions must be lists or tuples'),
 (([],[],'a','a'),ValueError,'state count must be between 1 and 32'),
 (([None]*33,[],'a','a'),ValueError,'state count must be between 1 and 32'),
 ((['a'],[None]*129,'a','a'),ValueError,'transition count must not exceed 128'),
 ((['a'],[None],'a','a'),ValueError,'transitions must have source action destination effort'),
 ((['a','a'],[],'a','a'),ValueError,'states must be unique'),
 ((['a'],[],'b','a'),ValueError,'start and goal must be known states'),
 ((['a'],[('a','go','b',1)],'a','a'),ValueError,'transition endpoints must be known states'),
 ((['a'],[('a','go','a',True)],'a','a'),TypeError,'effort must be nonbool int or Fraction'),
 ((['a'],[('a','go','a',-1)],'a','a'),ValueError,'effort must be nonnegative'),
 (([''],[],'',''),ValueError,'label length must be between 1 and 80'),
 (([' '],[],' ',' '),ValueError,'labels must not be blank'),
 (([True],[],'a','a'),TypeError,'labels must be strings'),
 ((['x'*81],[],'a','a'),ValueError,'label length must be between 1 and 80'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('value',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(value):
    with pytest.raises(ValueError,match='^effort must fit 32 bits$'):solve(['a'],[('a','x','a',value)],'a','a')


def test_eighty_character_label_admission():
    label='x'*80
    assert solve([label],[],label,label)['state_path']==[label]
