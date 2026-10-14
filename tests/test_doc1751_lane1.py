import random
import pytest
from sugarcode.extra_doc.structural1751 import audit_relations
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_adjacency_matrix_oracle():
    rng=random.Random(1751);nodes=list('abcde')
    for _ in range(100):
        rng.shuffle(nodes);edges=[(a,b) for a in nodes for b in nodes if rng.randrange(2)]
        matrix=[[int((a,b) in edges) for b in nodes] for a in nodes]
        degrees=[(n,sum(matrix[j][i] for j in range(5)),sum(matrix[i])) for i,n in enumerate(nodes)]
        reciprocal=sorted((a,b) for i,a in enumerate(nodes) for j,b in enumerate(nodes) if a<b and matrix[i][j] and matrix[j][i])
        assert audit_relations(nodes,edges)=={'degrees':degrees,'reciprocal_pairs':reciprocal,'claim':'PARTIAL','structure_validated':False}

@pytest.mark.parametrize('nodes',[None,L(['a']),('a',),[],list(map(str,range(101))),['a','a'],*[[x] for x in BAD]])
def test_nodes_invalid(nodes):
    with pytest.raises(ValueError) as exc:audit_relations(nodes,[])
    assert str(exc.value)=='nodes must be an exact list of 1..100 unique valid labels'

@pytest.mark.parametrize('edges,message',[
 *[(x,'edges must be an exact list with 0..100 entries') for x in (None,L(),(),[(str(i),'a') for i in range(101)])],
 *[([x],'edge must be a source target tuple') for x in (['a','b'],T(('a','b')),('a',),('a','b','c'))],
 *[([(x,'a')],'endpoints must be known valid labels') for x in (*BAD,'unknown')],
 *[([('a',x)],'endpoints must be known valid labels') for x in (*BAD,'unknown')],
 ([('a','b'),('a','b')],'edges must be unique'),
])
def test_edges_invalid(edges,message):
    with pytest.raises(ValueError) as exc:audit_relations(['a','b'],edges)
    assert str(exc.value)==message


def test_caps_loops_empty_and_label_caps():
    nodes=['x'*80]+list(map(str,range(99)));got=audit_relations(nodes,[(n,n) for n in nodes])
    assert got['degrees']==[(n,1,1) for n in nodes] and got['reciprocal_pairs']==[]
    assert audit_relations(['\u200b'],[])['degrees']==[('\u200b',0,0)]
