import copy
import itertools
import pytest
from sugarcode.extra_doc.metaphor_graph260 import generate


def args():return [dict(domain='research team',nodes=['lead','worker','reviewer'],edges=[['lead','guides','worker'],['reviewer','checks','worker'],['worker','informs','lead']]),[dict(domain='orchestra',nodes=['conductor','musician','listener'],edges=[['conductor','guides','musician'],['listener','checks','musician']])],[]]


def test_actual_generated_mapping_metaphor_explanation_limits_no_mutation():
    a=args();before=copy.deepcopy(a);r=generate(*a);c=r['candidates'][0]
    assert c['mapping']==dict(lead='conductor',worker='musician',reviewer='listener')
    assert c['metaphor']=='research team is orchestra: lead is conductor; worker is musician; reviewer is listener.'
    assert c['explanation']=='As lead guides worker, conductor guides musician. As reviewer checks worker, listener checks musician.'
    assert c['matched_edge_count']==2 and c['unmapped_target_edges']==[['worker','informs','lead']]
    assert c['matched_edges']==a[0]['edges'][:2] and c['fresh_domain_pairing_in_supplied_history'] and not c['universal_novelty_claimed'] and not c['reader_illumination_verified']
    assert r['review_required'] and r['external_effects']==[] and a==before


def test_history_same_domain_width_no_relation_and_lexicographic_tie_menu():
    a=args();a[2]=[['research team','orchestra']];assert generate(*a)['status']=='no_fresh_relational_match'
    a=args();a[1][0]['domain']='research team';assert generate(*a)['candidates']==[]
    a=args();a[1][0]['edges']=[['conductor','unrelated','musician']];assert generate(*a)['candidates']==[]
    a=args();a[1][0]['nodes'].append('extra');assert generate(*a)['candidates']==[]
    a=args();other=copy.deepcopy(a[1][0]);other['domain']='a domain';a[1].append(other)
    assert [c['source_domain'] for c in generate(*a)['candidates']]==['a domain','orchestra']
    assert generate(*a)['novelty_scope']=='only absence of exact domain pair in supplied history'


def test_200_independent_edge_overlap_search_by_index_permutations():
    from random import Random
    rng=Random(260)
    for _ in range(200):
        tn=['a','b','c'];sn=['x','y','z'];possible=[(i,r,j) for i in range(3) for j in range(3) if i!=j for r in ('links','checks')]
        target=rng.sample(possible,rng.randrange(1,7));source=rng.sample(possible,rng.randrange(1,7))
        scores=[]
        for p in itertools.permutations(range(3)):
            common=sum((p[i],r,p[j]) in source for i,r,j in target);scores.append((common,tuple(sn[j] for j in p)))
        count=max(s[0] for s in scores);mapping=min(s[1] for s in scores if s[0]==count)
        r=generate(dict(domain='target',nodes=tn,edges=[[tn[i],rel,tn[j]] for i,rel,j in target]),[dict(domain='source',nodes=sn,edges=[[sn[i],rel,sn[j]] for i,rel,j in source])],[])
        if not count:assert r['candidates']==[]
        else:
            c=r['candidates'][0];assert c['matched_edge_count']==count and tuple(c['mapping'][j] for j in tn)==mapping


def test_caps_edges_sources_history_and_text_boundaries():
    for n in (2,4):
        nodes=[str(i) for i in range(n)];edges=[[str(i),'links',str(j)] for i in range(n) for j in range(n) if i!=j]
        g=dict(domain='t',nodes=nodes,edges=edges);h=copy.deepcopy(g);h['domain']='s'
        assert generate(g,[h],[])['candidates'][0]['matched_edge_count']==len(edges)
    for n in (1,9,10):
        a=args();a[1]=[dict(a[1][0],domain=str(i)) for i in range(n)];assert len(generate(*a)['candidates'])==n
    a=args();a[0]['domain']='x'*80;a[2]=[['a','b']]*50;generate(*a)


def test_all_schema_types_caps_invalid_text_and_endpoints():
    for value in (None,True,{},dict(domain='x',nodes=[],edges=[],extra=1)):
        a=args();a[0]=value
        with pytest.raises(ValueError,match='^exact domain/nodes/edges graph fields$'):generate(*a)
    for nodes in (None,(),[],['a'],['a']*5):
        a=args();a[0]['nodes']=nodes
        with pytest.raises(ValueError,match='^2..4 graph nodes before scan$'):generate(*a)
    a=args();a[0]['nodes']=['a','a']
    with pytest.raises(ValueError,match='^unique graph nodes$'):generate(*a)
    for edges in (None,(),[],[['a','r','b']]*13):
        a=args();a[0]['edges']=edges
        with pytest.raises(ValueError,match='^1..12 relational edges before scan$'):generate(*a)
    for row in (None,(),[],['a'],['a']*4):
        a=args();a[0]['edges']=[row]
        with pytest.raises(ValueError,match='^edge source/relation/destination triple$'):generate(*a)
    for row in (['unknown','r','worker'],['lead','r','lead']):
        a=args();a[0]['edges']=[row]
        with pytest.raises(ValueError,match='^distinct graph endpoints in node menu$'):generate(*a)
    a=args();a[0]['edges']=[a[0]['edges'][0]]*2
    with pytest.raises(ValueError,match='^unique relational edges$'):generate(*a)
    for invalid in ('',True,None,'x'*81,' x','x ','x\n','x\u202e'):
        for slot in ('domain','node','relation'):
            a=args()
            if slot=='domain':a[0]['domain']=invalid
            elif slot=='node':a[0]['nodes'][0]=invalid
            else:a[0]['edges'][0][1]=invalid
            with pytest.raises(ValueError,match='^strict visible trimmed text 1..80 characters$'):generate(*a)
    for sources in (None,(),[],[{}]*11):
        a=args();a[1]=sources
        with pytest.raises(ValueError,match='^1..10 source graphs before scan$'):generate(*a)
    a=args();a[1]*=2
    with pytest.raises(ValueError,match='^unique source domain names$'):generate(*a)
    for previous in (None,(),[[]]*51):
        a=args();a[2]=previous
        with pytest.raises(ValueError,match='^0..50 previously used domain pairings before scan$'):generate(*a)
    for row in (None,(),[],['a'],['a']*3):
        a=args();a[2]=[row]
        with pytest.raises(ValueError,match='^previous target/source domain pairs$'):generate(*a)
