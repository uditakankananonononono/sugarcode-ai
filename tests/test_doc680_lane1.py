import itertools
import pytest
from sugarcode.extra_doc.clean_architecture680 import audit


def test_all_layer_pairs_independent_difference_oracle():
    layers={str(i):i for i in range(11)};edges=list(itertools.product(layers,repeat=2))*2
    got=audit(layers,edges)
    diffs=[int(b)-int(a) for a,b in edges]
    assert got['outward']==[i for i,d in enumerate(diffs) if d>0]
    assert got['same']==[i for i,d in enumerate(diffs) if not d]
    assert got['inward']==[i for i,d in enumerate(diffs) if d<0]
    assert got['claim']=='PARTIAL' and got['code_validated'] is False

class D(dict):pass
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass

@pytest.mark.parametrize('layers,edges,message',[
 (D(a=0),[],'layers must be an exact dict with 1..100 entries'),
 ({},[],'layers must be an exact dict with 1..100 entries'),
 *[({x:0},[],'IDs must be nonblank exact strings of 1..80 characters') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[({'a':x},[],'layers must be integers in 0..10') for x in (True,I(0),-1,11)],
 ({'a':0},L(),'edges must be an exact list with 0..500 entries'),
 ({'a':0},[T(('a','a'))],'edges must be exact known ID pair tuples'),
 ({'a':0},[(S('a'),'a')],'edges must be exact known ID pair tuples'),
 ({'a':0},[('a','b')],'edges must be exact known ID pair tuples'),
])
def test_invalid(layers,edges,message):
    with pytest.raises(ValueError) as exc:audit(layers,edges)
    assert str(exc.value)==message


def test_maxima_labels_and_zero_width():
    layers={str(i):10 for i in range(100)};edges=[('0','99')]*500
    assert audit(layers,edges)['same']==list(range(500))
    assert audit({'x'*80:0,'\u200b':10},[('x'*80,'\u200b')])['outward']==[0]
