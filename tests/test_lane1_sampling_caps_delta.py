import pytest
from sugarcode.extra_doc.permutation1024 import test as permutation
from sugarcode.extra_doc.robust1026 import summarize
from sugarcode.extra_doc.outlier1027 import detect
from sugarcode.extra_doc.mle1030 import estimate
from sugarcode.extra_doc.em1031 import step
from sugarcode.extra_doc.gibbs1034 import sweep

class L(list):pass

@pytest.mark.parametrize('call,message',[
 (lambda:permutation([1]*13,1),'values must be an exact list with 2..12 entries'),
 (lambda:summarize([1]*101),'values must be an exact list with 1..100 entries'),
 (lambda:detect([1]*101),'values must be an exact list with 4..100 entries'),
 (lambda:estimate(0,0,[(1,2)]),'trials must be an integer in 1..100'),
 (lambda:estimate(0,101,[(1,2)]),'trials must be an integer in 1..100'),
 (lambda:estimate(-1,5,[(1,2)]),'successes must be an integer in 0..trials'),
 (lambda:estimate(6,5,[(1,2)]),'successes must be an integer in 0..trials'),
 (lambda:estimate(0,1,[(i,100) for i in range(51)]),'grid must be an exact list with 1..50 entries'),
 (lambda:step([0]*51,(1,2),(1,2),(1,2)),'observations must be an exact list with 1..50 entries'),
 (lambda:sweep([[1,1],[1,1]],(0,0),((0,101),(0,1))),'draws must be exact integer fractions with 0<=num<den<=100'),
 (lambda:sweep([[1,1],[1,1]],(0,0),((0,1),(0,101))),'draws must be exact integer fractions with 0<=num<den<=100'),
 (lambda:sweep([L([1,1]),[1,1]],(0,0),((0,1),(0,1))),'weights must be an exact two by two list'),
 (lambda:sweep([[1,1],L([1,1])],(0,0),((0,1),(0,1))),'weights must be an exact two by two list'),
])
def test_upper_caps_and_refusals(call,message):
    with pytest.raises(ValueError) as exc:call()
    assert str(exc.value)==message


def test_accepted_endpoints():
    assert permutation([1]*12,1)['p']==(1,1)
    assert summarize([1]*100)['median']==(1,1)
    assert detect([1]*100)['outliers']==[]
    assert estimate(0,100,[(i,100) for i in range(50)])['index']==0
    assert step([0]*50,(1,100),(1,100),(99,100))['p1']==(0,1)
    assert sweep([[100,100],[100,100]],(0,0),((0,100),(0,100)))['state']==(1,1)
