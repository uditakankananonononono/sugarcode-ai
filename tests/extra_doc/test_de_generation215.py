import copy
import pytest
from sugarcode.extra_doc.de_generation215 import evolve


def args():return [[[4,1],[2,3],[-2,1],[0,-3]],[[-5,5],[-5,5]],[0,0],[[1,2,3],[0,2,3],[0,1,3],[0,1,2]],[[.5,.5]]*4,[0,1,0,1],.5,.5]


def test_independent_synchronous_mutation_crossover_forcing_selection_and_no_mutation():
    inputs=args();before=copy.deepcopy(inputs);r=evolve(*inputs)
    # Equality draw=.5 does not cross; each forced dimension does.
    assert r['trial_points_fraction']==[['1','1'],['2','3'],['5','1'],['0','2']]
    assert r['population_fraction']==[['1','1'],['2','3'],['-2','1'],['0','2']]
    assert r['accepted']==[True,False,False,True] and r['best_index']==0
    assert r['best_point_fraction']==['1','1'] and r['best_loss_fraction']=='2'
    assert inputs==before and not r['global_optimum_verified'] and not r['random_sampling_verified'] and r['external_effects']==[]


def test_full_crossover_zero_cr_forcing_clip_and_tie_retention():
    inputs=args();inputs[-1]=1;r=evolve(*inputs)
    assert r['trial_points_fraction'][0]==['1','5'] # mutant y5 clipped from5 exactboundary
    inputs=args();inputs[-1]=0;r=evolve(*inputs)
    assert r['trial_points_fraction'][0]==['1','1']
    inputs=args();inputs[-2]=2;inputs[-1]=1;r=evolve(*inputs)
    assert r['trial_points_fraction'][0]==['-2','5']
    inputs=[[[0]]*4,[[-1,1]],[0],[[1,2,3],[0,2,3],[0,1,3],[0,1,2]],[[0]]*4,[0]*4,0,0]
    assert evolve(*inputs)['accepted']==[False]*4


@pytest.mark.parametrize('n',[3,4,19,20,21])
def test_population_caps(n):
    inputs=[[[0]]*n,[[-1,1]],[0],[[j for j in range(n) if j!=i][:3] for i in range(n)],[[0]]*n,[0]*n,0,0]
    if 4<=n<=20:assert len(evolve(*inputs)['accepted'])==n
    else:
        with pytest.raises(ValueError,match='^4..20 population points before scan$'):evolve(*inputs)
@pytest.mark.parametrize('d',[0,1,7,8,9])
def test_dimension_caps(d):
    inputs=[[[0]*d]*4,[[-1,1]]*d,[0]*d,[[1,2,3],[0,2,3],[0,1,3],[0,1,2]],[[0]*d]*4,[0]*4,0,0]
    if 1<=d<=8:assert len(evolve(*inputs)['best_point_fraction'])==d
    else:
        with pytest.raises(ValueError,match='^1..8 target dimensions before scan$'):evolve(*inputs)


def test_numeric_edges_strict_types_and_all_range_refusals():
    for v in (-1000,1000,-1000.0,1000.0):
        inputs=[[[v]]*4,[[-1000,1000]],[v],[[1,2,3],[0,2,3],[0,1,3],[0,1,2]],[[0]]*4,[0]*4,0,0];evolve(*inputs)
    for f in (0,2,2.0):inputs=args();inputs[-2]=f;evolve(*inputs)
    for cr in (0,1,1.0):inputs=args();inputs[-1]=cr;evolve(*inputs)
    for draw in (0,1,1.0):inputs=args();inputs[4]=[[draw,draw]]*4;evolve(*inputs)
    for bad in (True,'1',None,-1001,1001,float('nan'),float('inf')):
        for index in (0,2):
            inputs=args()
            if index==0:inputs[0][0][0]=bad
            else:inputs[2][0]=bad
            with pytest.raises(ValueError,match='^strict finite bounded DE number$'):evolve(*inputs)
    for index in (6,7,4):
        for bad in (True,'1',None,-.1,3,float('nan')):
            inputs=args();inputs[index]=bad if index!=4 else [[bad,0]]*4
            with pytest.raises(ValueError,match='^strict finite bounded DE number$'):evolve(*inputs)


def test_shapes_donor_self_duplicate_type_forcedcoordinate_and_bounds_refusals():
    for index in (0,4):
        for bad in ((),None,True,[[0]],[[0,0]]*3):
            inputs=args();inputs[index]=bad
            msg='4..20 population points before scan' if index==0 and (type(bad) is not list or len(bad)<4) else 'aligned population matrix dimensions'
            with pytest.raises(ValueError,match='^'+msg+'$'):evolve(*inputs)
    for bad in ([],(),None,[[0]],[[0,1,2]]):
        inputs=args();inputs[1]=bad
        with pytest.raises(ValueError,match='^one ordered bound pair per dimension$'):evolve(*inputs)
    inputs=args();inputs[1]=[[0,0],[-5,5]]
    with pytest.raises(ValueError,match='^strictly ordered DE bounds$'):evolve(*inputs)
    inputs=args();inputs[1]=[[-1,1],[-1,1]]
    with pytest.raises(ValueError,match='^population inside bounds$'):evolve(*inputs)
    for row in ([0,1,2],[1,1,2],[1,2,4],[True,2,3],(1,2,3),[1,2]):
        inputs=args();inputs[3][0]=row
        with pytest.raises(ValueError,match='^three distinct nonself donor indices per point$'):evolve(*inputs)
    for bad in ([],(),None,[0,0,0],[True,0,0,0],[2,0,0,0],[-1,0,0,0]):
        inputs=args();inputs[5]=bad
        with pytest.raises(ValueError,match='^one strict forced coordinate per point$'):evolve(*inputs)


def test_nonzero_target_squared_difference_not_sum():
    inputs=args();inputs[2]=[1,1]
    result=evolve(*inputs)
    assert result['best_loss_fraction']=='0' and result['best_point_fraction']==['1','1']


@pytest.mark.parametrize('index',[4,7])
def test_probability_upper_cap_plus_decimal_refused(index):
    inputs=args();inputs[index]=1.1 if index==7 else [[1.1,0]]*4
    with pytest.raises(ValueError,match='^strict finite bounded DE number$'):evolve(*inputs)


@pytest.mark.parametrize('which,value',[(0,-1001),(1,1001)])
def test_each_bound_endpoint_numerical_cap_refused(which,value):
    inputs=args();inputs[1][0][which]=value
    with pytest.raises(ValueError,match='^strict finite bounded DE number$'):evolve(*inputs)
