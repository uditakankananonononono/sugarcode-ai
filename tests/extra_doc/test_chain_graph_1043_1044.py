import itertools
import random
import string
from fractions import Fraction
import pytest
from sugarcode.extra_doc import chain_crf as c
from sugarcode.extra_doc import undirected_separation as g

class L(list): pass
class D(dict): pass
class S(str): pass
class I(int): pass


def crf_data():
    return {'labels': ['a','b'], 'unary': [[2,1],[1,3]], 'transition': [[2,1],[1,2]]}


def graph_data():
    return {'nodes': ['a','b','c','d'], 'edges': [['a','b'],['b','c']], 'given': ['b'], 'source':'a', 'target':'c'}


def crf_oracle(data):
    paths=list(itertools.product(range(len(data['labels'])), repeat=len(data['unary'])))
    weights=[]
    for path in paths:
        w=1
        for t,s in enumerate(path): w*=data['unary'][t][s]
        for a,b in zip(path,path[1:]): w*=data['transition'][a][b]
        weights.append(w)
    z=sum(weights)
    best=paths[weights.index(max(weights))]
    return {'partition':z,'map':[data['labels'][s] for s in best], 'map_probability':list(Fraction(max(weights),z).as_integer_ratio()),
        'marginals':[[list(Fraction(sum(w for p,w in zip(paths,weights) if p[t]==s),z).as_integer_ratio()) for s in range(len(data['labels']))] for t in range(len(data['unary']))], 'claims': [False]*4}


def graph_oracle(data):
    remaining=set(data['nodes'])-set(data['given'])
    adj={v:set() for v in remaining}
    for a,b in data['edges']:
        if a in remaining and b in remaining: adj[a].add(b); adj[b].add(a)
    def paths(a,b):
        answer=[]
        def walk(p):
            if p[-1]==b: answer.append(p); return
            for n in sorted(adj[p[-1]]-set(p)): walk(p+[n])
        walk([a])
        return answer
    allpaths=paths(data['source'],data['target'])
    comps=[]
    while remaining:
        a=min(remaining)
        group=sorted(n for n in remaining if n==a or paths(a,n))
        comps.append(group); remaining-=set(group)
    return {'separated':not bool(allpaths), 'path':min(allpaths,key=lambda p:(len(p),p)) if allpaths else [], 'components':comps, 'claims':[False]*4}


def test_hand():
    x=crf_data(); assert c.infer_chain(x)==crf_oracle(x)
    assert c.infer_chain(x)['partition']==17
    assert c.infer_chain(x)['map']==['a','b']
    assert c.infer_chain(x)['map_probability']==[6,17]
    assert g.separate(graph_data())=={'separated':True,'path':[], 'components':[['a'],['c'],['d']], 'claims':[False]*4}


def test_random_oracles():
    r=random.Random(1743)
    for n in (2,3,4):
        for size in range(1,6):
            for _ in range(5):
                x={'labels':list('abcd'[:n]),'unary':[[r.randint(1,9) for _ in range(n)] for _ in range(size)],'transition':[[r.randint(1,9) for _ in range(n)] for _ in range(n)]}
                assert c.infer_chain(x)==crf_oracle(x)
    for _ in range(80):
        nodes=list('abcde'); x={'nodes':nodes, 'edges':[list(e) for e in itertools.combinations(nodes,2) if r.choice([0,1])], 'given':r.sample(['b','c','d'],r.randrange(4)), 'source':'a','target':'e'}
        assert g.separate(x)==graph_oracle(x)


def test_bounds_ties_order_and_freshness():
    x={'labels':['z','a'], 'unary':[[1,1]]*6, 'transition':[[1,1],[1,1]]}
    assert c.infer_chain(x)==crf_oracle(x)
    assert c.infer_chain(x)['map']==['z']*6
    y={'nodes':list('abcdefghijkl'), 'edges':[], 'given':[], 'source':'a','target':'l'}
    assert g.separate(y)==graph_oracle(y)
    y={'nodes':['d','c','b','a'], 'edges':[['a','c'],['c','d'],['a','b'],['b','d']], 'given':[], 'source':'a','target':'d'}
    assert g.separate(y)==graph_oracle(y)
    assert g.separate(y)['path']==['a','b','d']
    for fn,make in [(c.infer_chain,crf_data),(g.separate,graph_data)]:
        x=make(); result=fn(x); result['claims'][0]=True
        assert fn(x)['claims']==[False]*4
        assert x==make()


@pytest.mark.parametrize('module,fn,make',[(c,c.infer_chain,crf_data),(g,g.separate,graph_data)])
def test_outer(module,fn,make):
    for x in [None,[],D(make()),{},dict(make(),extra=1)]:
        with pytest.raises(ValueError):fn(x)


@pytest.mark.parametrize('field',['labels','unary','transition'])
def test_crf_containers(field):
    for transform in [tuple,L]:
        x=crf_data(); x[field]=transform(x[field])
        with pytest.raises(ValueError):c.infer_chain(x)
    if field!='labels':
        for pos in range(len(crf_data()[field])):
            for transform in [tuple,L]:
                x=crf_data(); x[field][pos]=transform(x[field][pos])
                with pytest.raises(ValueError):c.infer_chain(x)


@pytest.mark.parametrize('field',['nodes','edges','given'])
def test_graph_containers(field):
    for transform in [tuple,L]:
        x=graph_data();x[field]=transform(x[field])
        with pytest.raises(ValueError):g.separate(x)
    if field=='edges':
        for pos in range(2):
            for transform in [tuple,L]:
                x=graph_data();x[field][pos]=transform(x[field][pos])
                with pytest.raises(ValueError):g.separate(x)


def test_crf_numeric_every_slot():
    for field in ['unary','transition']:
        for i in range(2):
            for j in range(2):
                for val in [True,1.0,I(1),0,10,-1,'1',None]:
                    x=crf_data();x[field][i][j]=val
                    with pytest.raises(ValueError):c.infer_chain(x)


def test_crf_shapes():
    for field, values in [('labels',[[],['a'],list('abcde'),['a','a']]),('unary',[[],[[1,1]]*7,[[1]],[[1,1,1]]]),('transition',[[],[[1,1]],[[1,1]]*3,[[1],[1,1]],[[1,1],[1,1,1]]])]:
        for value in values:
            x=crf_data();x[field]=value
            with pytest.raises(ValueError):c.infer_chain(x)


def test_graph_shapes_references():
    cases=[('nodes',[]),('nodes',['a']),('nodes',list('abcdefghijklm')),('nodes',['a','a']),('edges',[['a']]),('edges',[['a','b','c']]),('edges',[['a','a']]),('edges',[['a','z']]),('edges',[['a','b'],['b','a']]),('edges',[['a','b']]*31),('given',['b']*13),('given',['b','b']),('given',['z']),('source','z'),('target','a'),('given',['a']),('given',['c'])]
    for field,value in cases:
        x=graph_data();x[field]=value
        with pytest.raises(ValueError):g.separate(x)


def test_nonascii_and_all_label_slots():
    bad=[S('a'),'','abcdefghi',True,None]+[ch for ch in string.printable if ch not in string.ascii_lowercase]+['é','Ω','中','а','𝚊','a\u200b']
    slots=[('labels',0),('labels',1)]
    for field,pos in slots:
        for val in bad:
            x=crf_data();x[field][pos]=val
            with pytest.raises(ValueError):c.infer_chain(x)
    slots=[('nodes',i,None) for i in range(4)]+[('edges',i,j) for i in range(2) for j in range(2)]+[('given',0,None),('source',None,None),('target',None,None)]
    for field,i,j in slots:
        for val in bad:
            x=graph_data()
            if i is None:x[field]=val
            elif j is None:x[field][i]=val
            else:x[field][i][j]=val
            with pytest.raises(ValueError):g.separate(x)


def test_contract_exact():
    assert c.ALPHABET==g.ALPHABET=='abcdefghijklmnopqrstuvwxyz'
    assert c.SCOPE=='PARTIAL: exact positive-integer linear-chain CRF inference only'
    assert g.SCOPE=='PARTIAL: undirected graph separation only'
    assert c.NOT_CLAIMED==('parameter training','feature extraction','general graph inference','production readiness')
    assert g.NOT_CLAIMED==('directed causal inference','probability estimation','graph learning','production readiness')


def test_label_length_and_internal_charset():
    x=crf_data();x['labels']=['abcdefgh','z'];assert c.infer_chain(x)==crf_oracle(x)
    y=graph_data();y['nodes'][3]='abcdefgh';assert g.separate(y)==graph_oracle(y)
    for char in [p for p in string.printable if p not in string.ascii_lowercase]+['é','中','𝚊','а']:
        for label in [char+'a','a'+char+'b','a'+char]:
            x=crf_data();x['labels'][1]=label
            with pytest.raises(ValueError):c.infer_chain(x)
            y=graph_data();y['nodes'][3]=label
            with pytest.raises(ValueError):g.separate(y)


def test_late_matrix_shape_and_label_errors():
    for field in ['unary','transition']:
        x=crf_data();x[field][-1]=[1]
        with pytest.raises(ValueError):c.infer_chain(x)
    x=graph_data();x['given']=['b',S('d')]
    with pytest.raises(ValueError):g.separate(x)
    x=graph_data();x['edges']=[['a','b'],['c']]
    with pytest.raises(ValueError):g.separate(x)


def test_crf_label_caps_with_valid_matrix_shapes():
    for n in [1,5]:
        x={'labels':list('abcde'[:n]), 'unary':[[1]*n], 'transition':[[1]*n for _ in range(n)]}
        with pytest.raises(ValueError):c.infer_chain(x)


def test_guard_order_and_saturated_edges():
    x=crf_data();x['unary']=L(x['unary'])
    with pytest.raises(ValueError,match='^unary must be a list of 1..6 rows$'):c.infer_chain(x)
    for n in [1]:
        x={'nodes':['a']*n, 'edges':[], 'given':[], 'source':'a','target':'b'}
        with pytest.raises(ValueError,match='^nodes must be a list of 2..12 identifiers$'):g.separate(x)
    x={'nodes':['a','b'], 'edges':[], 'given':[], 'source':'a','target':'b'}
    assert g.separate(x)==graph_oracle(x)
    nodes=list('abcdefghi')
    for size in [30,31]:
        x={'nodes':nodes, 'edges':[list(e) for e in list(itertools.combinations(nodes,2))[:size]], 'given':[], 'source':'a','target':'i'}
        if size==30: assert g.separate(x)==graph_oracle(x)
        else:
            with pytest.raises(ValueError,match='^edges must be a list of 0..30 pairs$'):g.separate(x)
    for size in [12,13]:
        x=graph_data();x['given']=['b']*size
        message='conditioned nodes must be unique' if size==12 else 'given must be a list of 0..12 identifiers'
        with pytest.raises(ValueError,match='^'+message+'$'):g.separate(x)


def test_map_ties_different_state_and_path():
    r=random.Random(991)
    for _ in range(250):
        x={'labels':['z','a'], 'unary':[[r.randint(1,3) for s in range(2)] for t in range(3)], 'transition':[[r.randint(1,3) for s in range(2)] for t in range(2)]}
        assert c.infer_chain(x)==crf_oracle(x)


def test_cross_container_subclasses_and_max_sites():
    x=crf_data();x['unary']=[[1,1]]*6;assert c.infer_chain(x)==crf_oracle(x)
    x=crf_data();x['unary']=[[1,1]]*7
    with pytest.raises(ValueError):c.infer_chain(x)
    x=graph_data();x['given']=['b','d'];assert g.separate(x)==graph_oracle(x)
    x=graph_data();x['given']=['b',S('d')]
    with pytest.raises(ValueError):g.separate(x)
