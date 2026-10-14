import pytest
from sugarcode.extra_doc.competitive_analysis import competitive_map as solve


def test_explicit_strength_weakness_parity_weighted_rank_oracle():
    assert solve([[4,1,3],[2,4,3],[4,1,3]],[2,2,3],[1,3,0])=={
      'competitors':[{'strengths':[0],'weaknesses':[1],'parity':[2],'weighted_delta':-1},
                     {'strengths':[1],'weaknesses':[],'parity':[0,2],'weighted_delta':6},
                     {'strengths':[0],'weaknesses':[1],'parity':[2],'weighted_delta':-1}],
      'ranking':[1,0,2],'scores_verified':False}


def test_max_caps_and_zero_scores():
    assert solve([[1000]*16]*16,[0]*16,[1000]*16)['competitors'][0]['weighted_delta']==16000000
    assert solve([[0]],[0],[1])['competitors'][0]['parity']==[0]

@pytest.mark.parametrize('args,error,message',[
 ((None,[],[]),TypeError,'inputs must be lists or tuples'),
 (([],[0],[1]),ValueError,'competitor and criterion counts must be between 1 and 16'),
 (([None]*17,[0],[1]),ValueError,'competitor and criterion counts must be between 1 and 16'),
 (([[0]],[],[]),ValueError,'competitor and criterion counts must be between 1 and 16'),
 (([[0]],[0]*17,[1]*17),ValueError,'competitor and criterion counts must be between 1 and 16'),
 (([[0]],[0],[]),ValueError,'criterion shapes must agree'),
 (([None],[0],[1]),ValueError,'criterion shapes must agree'),
 (([[0]],[0],[0]),ValueError,'at least one weight must be positive'),
])
def test_shape_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('bad',[True,-1,1001,None,1.0])
@pytest.mark.parametrize('slot',[0,1,2])
def test_exact_scalar_rejection(bad,slot):
    args=[[[0]],[0],[1]]
    args[slot]=[[bad]] if slot==0 else [bad]
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)=='scores and weights must be nonbool integers zero through 1000'

@pytest.mark.parametrize('scores,weights',[
 ([[1]],[1,1]),([[1,2,3]],[1,1]),([[1,2]],[1]),([[1,2]],[1,1,1]),
])
def test_short_long_criterion_shapes(scores,weights):
    with pytest.raises(ValueError) as exc:solve(scores,[1,1],weights)
    assert str(exc.value)=='criterion shapes must agree'
