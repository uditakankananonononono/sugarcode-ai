import copy
import itertools
import pytest
from sugarcode.extra_doc.data_lineage import lineage_sources
class L(list): pass
class T(tuple): pass
class I(int): pass

@pytest.mark.parametrize('container',[L,T])
def test_subclass_containers(container):
    with pytest.raises(TypeError,match='^inputs must be a list or tuple$'):
        lineage_sources(container([[],[0]]))
    with pytest.raises(ValueError,match='^datasets must contain at most 32 input indices$'):
        lineage_sources([[],container([0])])

@pytest.mark.parametrize('bad',[I(0),True,1.0,-1,3,None,'0'])
def test_nonfirst_mixed_invalid_index(bad):
    with pytest.raises(ValueError,match='^inputs must contain nonbool valid nonself indices$'):
        lineage_sources([[],[],[0,bad]])


def test_nonadjacent_duplicate_and_cycle_exact():
    with pytest.raises(ValueError,match='^input indices must be unique$'):
        lineage_sources([[],[],[0,1,0]])
    with pytest.raises(ValueError,match='^lineage graph must be acyclic$'):
        lineage_sources([[],[3],[1],[2]])
    with pytest.raises(ValueError,match='^datasets must contain at most 32 input indices$'):
        lineage_sources([[],[0]*33])

@pytest.mark.parametrize('outer',[list,tuple])
@pytest.mark.parametrize('row',[list,tuple])
def test_plain_containers_full_keys_and_unchanged(outer,row):
    inputs=outer(row(r) for r in [[],[0],[0,1],[2]]);before=copy.deepcopy(inputs)
    assert lineage_sources(inputs)=={'ultimate_sources':[[0],[0],[0],[0]],
                                     'downstream_impact':[[1,2,3],[2,3],[3],[]],
                                     'lineage_validated':False}
    assert inputs==before
    assert lineage_sources(outer([row([])]))=={'ultimate_sources':[[0]],'downstream_impact':[[]],'lineage_validated':False}


def test_max_dense_dag_and_last_index():
    inputs=[list(range(i)) for i in range(32)]
    assert lineage_sources(inputs)=={'ultimate_sources':[[0] for _ in range(32)],
                                     'downstream_impact':[list(range(i+1,32)) for i in range(32)],
                                     'lineage_validated':False}
    result=lineage_sources([[31]]+[[] for _ in range(31)])
    assert result['ultimate_sources'][0]==[31] and result['downstream_impact'][31]==[0]


def test_all_small_dags_against_reachability_oracle():
    for n in range(1,5):
        edges=[(i,j) for i in range(n) for j in range(i)]
        for bits in itertools.product((False,True),repeat=len(edges)):
            inputs=[[] for _ in range(n)]
            for (i,j),included in zip(edges,bits):
                if included: inputs[i].append(j)
            paths=[]
            for i in range(n):
                reachable=set(); todo=list(inputs[i])
                while todo:
                    j=todo.pop()
                    if j in reachable:continue
                    reachable.add(j);todo.extend(inputs[j])
                paths.append(reachable)
            roots={i for i in range(n) if not inputs[i]}
            expected={'ultimate_sources':[sorted(({i}|paths[i]) & roots) for i in range(n)],
                      'downstream_impact':[[j for j in range(n) if i in paths[j]] for i in range(n)],
                      'lineage_validated':False}
            assert lineage_sources(inputs)==expected
