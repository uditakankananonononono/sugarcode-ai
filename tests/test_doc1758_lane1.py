import random
import pytest
from sugarcode.extra_doc.actor_network1758 import audit_network
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_boolean_floyd_warshall_oracle():
    rng=random.Random(1758)
    for _ in range(100):
        entities=[(str(i),rng.choice(['human','nonhuman'])) for i in range(8)];links=[(a,b) for a,k in entities for b,j in entities if a!=b and rng.randrange(4)==0]
        reach=[[i==j or (str(i),str(j)) in links for j in range(8)] for i in range(8)]
        for k in range(8):
            for i in range(8):
                for j in range(8):reach[i][j]=reach[i][j] or (reach[i][k] and reach[k][j])
        expected=[(str(i),[str(j) for j in range(8) if i!=j and reach[i][j]]) for i in range(8)]
        assert audit_network(entities,links)=={'reachable':expected,'kinds':entities,'claim':'PARTIAL','agency_inferred':False,'theory_validated':False}

@pytest.mark.parametrize('entities,message',[
 *[(x,'entities must be an exact list with 2..20 entries') for x in (None,L([('a','human'),('b','nonhuman')]),(('a','human'),('b','nonhuman')),[],[('a','human')],[(str(i),'human') for i in range(21)])],
 *[([x,('b','human')],'entity must be an id kind tuple') for x in (['a','human'],T(('a','human')),('a',),('a','human',1))],
 *[([(x,'human'),('b','human')],'entity IDs must be unique valid labels') for x in BAD],
 ([('a','human'),('a','nonhuman')],'entity IDs must be unique valid labels'),
 *[([('a',x),('b','human')],'kind must be an exact human or nonhuman string') for x in (None,True,1,S('human'),'Human','other','')],
])
def test_entities_invalid(entities,message):
    with pytest.raises(ValueError) as exc:audit_network(entities,[])
    assert str(exc.value)==message

@pytest.mark.parametrize('links,message',[
 *[(x,'links must be an exact list with 0..100 entries') for x in (None,L(),(),[('a','b')]*101)],
 *[([x],'link must be a source target tuple') for x in (['a','b'],T(('a','b')),('a',),('a','b','c'))],
 *[([(x,'b')],'endpoints must be distinct known valid labels') for x in (*BAD,'unknown','b')],
 *[([('a',x)],'endpoints must be distinct known valid labels') for x in (*BAD,'unknown','a')],
 ([('a','b'),('a','b')],'links must be unique'),
])
def test_links_invalid(links,message):
    with pytest.raises(ValueError) as exc:audit_network([('a','human'),('b','nonhuman')],links)
    assert str(exc.value)==message


def test_caps_labels_isolates_chain_and_cycles():
    entities=[('x'*80,'human'),('\u200b','nonhuman')]+[(str(i),'human') for i in range(18)];edges=[(a,b) for a,k in entities for b,j in entities if a!=b][:100]
    assert len(audit_network(entities,edges)['reachable'])==20
    assert audit_network([('a','human'),('b','nonhuman'),('c','human')],[('a','b'),('b','c')])['reachable']==[('a',['b','c']),('b',['c']),('c',[])]
    assert audit_network([('a','human'),('b','nonhuman')],[('a','b'),('b','a')])['reachable']==[('a',['b']),('b',['a'])]
