import random
import pytest
from sugarcode.extra_doc.social_network1759 import audit_graph
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_boolean_closure_and_triangle_oracle():
    rng=random.Random(1759)
    for _ in range(100):
        nodes=list('abcdefgh');rng.shuffle(nodes);edges=[(a,b) for a in nodes for b in nodes if a<b and rng.randrange(4)==0]
        matrix=[[int((a,b) in edges or (b,a) in edges) for b in nodes] for a in nodes];closure=[[bool(matrix[i][j]) or i==j for j in range(8)] for i in range(8)]
        for k in range(8):
            for i in range(8):
                for j in range(8):closure[i][j]=closure[i][j] or (closure[i][k] and closure[k][j])
        components=sorted({tuple(sorted(nodes[j] for j in range(8) if closure[i][j])) for i in range(8)})
        triangles=sorted((a,b,c) for i,a in enumerate(nodes) for j,b in enumerate(nodes) for k,c in enumerate(nodes) if a<b<c and matrix[i][j]*matrix[i][k]*matrix[j][k])
        assert audit_graph(nodes,edges)=={'degrees':[(n,sum(matrix[i])) for i,n in enumerate(nodes)],'components':[list(c) for c in components],'triangles':triangles,'claim':'PARTIAL','social_inference':False}

@pytest.mark.parametrize('nodes',[None,L(['a','b']),('a','b'),[],['a'],list(map(str,range(21))),['a','a'],*[[x,'b'] for x in BAD]])
def test_nodes_invalid(nodes):
    with pytest.raises(ValueError) as exc:audit_graph(nodes,[])
    assert str(exc.value)=='nodes must be an exact list of 2..20 unique valid labels'

@pytest.mark.parametrize('edges,message',[
 *[(x,'edges must be an exact list with 0..100 entries') for x in (None,L(),(),[('a','b')]*101)],
 *[([x],'edge must be a source target tuple') for x in (['a','b'],T(('a','b')),('a',),('a','b','c'))],
 *[([(x,'b')],'endpoints must be distinct known valid labels') for x in (*BAD,'unknown','b')],
 *[([('a',x)],'endpoints must be distinct known valid labels') for x in (*BAD,'unknown','a')],
 ([('a','b'),('a','b')],'undirected edges must be unique'),
 ([('a','b'),('b','a')],'undirected edges must be unique'),
])
def test_edges_invalid(edges,message):
    with pytest.raises(ValueError) as exc:audit_graph(['a','b'],edges)
    assert str(exc.value)==message


def test_caps_isolates_and_reverse_edge():
    nodes=['x'*80,'\u200b']+list(map(str,range(18)));edges=[(a,b) for a in nodes for b in nodes if a<b][:100]
    assert len(audit_graph(nodes,edges)['degrees'])==20
    assert audit_graph(['a','b'],[('b','a')])['degrees']==[('a',1),('b',1)]
    assert audit_graph(['b','a'],[])['components']==[['a'],['b']]
