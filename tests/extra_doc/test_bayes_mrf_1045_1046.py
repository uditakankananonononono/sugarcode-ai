import copy
import itertools
import random
import string
from fractions import Fraction
import pytest
from sugarcode.extra_doc import binary_bayes_net as b
from sugarcode.extra_doc import binary_pairwise_mrf as m

class L(list): pass
class D(dict): pass
class S(str): pass
class I(int): pass


def bd():
    return {'nodes':['a','b','c'], 'parents':[[],['a'],['b','a']], 'cpt':[[30],[20,80],[10,40,60,90]], 'evidence':{'c':1}}


def md():
    return {'nodes':['a','b','c'], 'unary':[[1,2],[3,1],[2,1]], 'factors':[['a','b',[2,3,1,4]],['c','b',[1,2,3,4]]]}


def bo(x):
    # Recursive branching of the probability tree, not the implementation's product loop.
    leaves=[]
    def descend(assignment, probability):
        if len(assignment)==len(x['nodes']):
            if all(assignment[k]==v for k,v in x['evidence'].items()):leaves.append((assignment.copy(), probability))
            return
        i=len(assignment); node=x['nodes'][i]
        parent_pattern=''.join(str(assignment[p]) for p in x['parents'][i])
        p=Fraction(x['cpt'][i][int(parent_pattern or '0',2)],100)
        for bit,q in [(0,1-p),(1,p)]:
            assignment[node]=bit;descend(assignment,probability*q);del assignment[node]
    descend({},Fraction(1))
    z=sum(p for a,p in leaves)
    def pair(f):return [f.numerator,f.denominator]
    return {'evidence_probability':pair(z),'posterior':{node:pair(sum(p for a,p in leaves if a[node])/z) for node in x['nodes']},'claims':[False]*4}


def mo(x):
    # Table join in assignment-key space, combining each factor independently.
    nodes=x['nodes'];table={tuple(bits):1 for bits in itertools.product([0,1],repeat=len(nodes))}
    for i,row in enumerate(x['unary']):
        table={bits:weight*row[bits[i]] for bits,weight in table.items()}
    for left,right,values in x['factors']:
        lookup=dict(zip(itertools.product([0,1],repeat=2),values))
        a,b=nodes.index(left),nodes.index(right)
        table={bits:weight*lookup[(bits[a],bits[b])] for bits,weight in table.items()}
    z=sum(table.values());best=min(table,key=lambda bits:(-table[bits],bits))
    def pair(f):return [f.numerator,f.denominator]
    return {'partition':z,'marginals':{node:pair(Fraction(sum(w for bits,w in table.items() if bits[i]),z)) for i,node in enumerate(nodes)},'map':list(best),'map_probability':pair(Fraction(table[best],z)),'claims':[False]*4}


def test_hand():
    x={'nodes':['a','b'],'parents':[[],['a']],'cpt':[[25],[10,70]],'evidence':{'b':1}}
    assert b.infer(x)==bo(x)=={'evidence_probability':[1,4],'posterior':{'a':[7,10],'b':[1,1]},'claims':[False]*4}
    x={'nodes':['a','b'],'unary':[[1,2],[3,1]],'factors':[['a','b',[2,3,1,4]]]}
    assert m.infer(x)==mo(x)=={'partition':23,'marginals':{'a':[14,23],'b':[11,23]},'map':[1,1],'map_probability':[8,23],'claims':[False]*4}


def test_random_oracles():
    r=random.Random(1045)
    for n in range(2,7):
        for _ in range(30):
            nodes=list('abcdef'[:n]);parents=[r.sample(nodes[:i],r.randint(0,i)) for i in range(n)]
            x={'nodes':nodes,'parents':parents,'cpt':[[r.randint(1,99) for _ in range(2**len(p))] for p in parents],'evidence':{k:r.randint(0,1) for k in r.sample(nodes,r.randint(0,n))}}
            assert b.infer(x)==bo(x)
            y={'nodes':nodes,'unary':[[r.randint(1,9),r.randint(1,9)] for _ in nodes],'factors':[]}
            for a,c in itertools.combinations(nodes,2):
                if r.randrange(2):
                    if r.randrange(2):a,c=c,a
                    y['factors'].append([a,c,[r.randint(1,9) for _ in range(4)]])
            assert m.infer(y)==mo(y)


def test_caps_ties_empty_evidence_and_factors():
    for n in [2,6]:
        nodes=list('abcdef'[:n]);x={'nodes':nodes,'parents':[[] for _ in nodes],'cpt':[[50] for _ in nodes],'evidence':{}}
        assert b.infer(x)==bo(x);assert b.infer(x)['evidence_probability']==[1,1]
        x['evidence']={k:i%2 for i,k in enumerate(nodes)};assert b.infer(x)==bo(x)
        y={'nodes':nodes,'unary':[[1,1] for _ in nodes],'factors':[]};assert m.infer(y)==mo(y);assert m.infer(y)['map']==[0]*n
    nodes=list('abcdef');y={'nodes':nodes,'unary':[[1,1] for _ in nodes],'factors':[[a,c,[1,1,1,1]] for a,c in itertools.combinations(nodes,2)]}
    assert len(y['factors'])==15;assert m.infer(y)==mo(y)
    for fn,make in [(b.infer,bd),(m.infer,md)]:
        x=make();snapshot=copy.deepcopy(x);out=fn(x);out['claims'][0]=True
        assert fn(x)['claims']==[False]*4;assert x==snapshot


@pytest.mark.parametrize('fn,make',[(b.infer,bd),(m.infer,md)])
def test_outer_types(fn,make):
    for x in [None,[],D(make()),{},dict(make(),extra=1)]:
        with pytest.raises(ValueError):fn(x)


@pytest.mark.parametrize('field',['nodes','parents','cpt'])
def test_b_containers(field):
    for transform in [L,tuple]:
        x=bd();x[field]=transform(x[field])
        with pytest.raises(ValueError):b.infer(x)
    if field!='nodes':
        for i in range(3):
            for transform in [L,tuple]:
                x=bd();x[field][i]=transform(x[field][i])
                with pytest.raises(ValueError):b.infer(x)
    x=bd();x['evidence']=D(x['evidence'])
    with pytest.raises(ValueError):b.infer(x)


@pytest.mark.parametrize('field',['nodes','unary','factors'])
def test_m_containers(field):
    for transform in [L,tuple]:
        x=md();x[field]=transform(x[field])
        with pytest.raises(ValueError):m.infer(x)
    if field!='nodes':
        for i in range(len(md()[field])):
            for transform in [L,tuple]:
                x=md();x[field][i]=transform(x[field][i])
                with pytest.raises(ValueError):m.infer(x)
    for i in range(2):
        for transform in [L,tuple]:
            x=md();x['factors'][i][2]=transform(x['factors'][i][2])
            with pytest.raises(ValueError):m.infer(x)


def test_numeric_every_slot():
    for i,row in enumerate(bd()['cpt']):
        for j in range(len(row)):
            for val in [True,I(50),50.0,0,100,'50',None]:
                x=bd();x['cpt'][i][j]=val
                with pytest.raises(ValueError):b.infer(x)
    for node in bd()['nodes']:
        for val in [True,I(1),1.0,-1,2,'1',None]:
            x=bd();x['evidence']={node:val}
            with pytest.raises(ValueError):b.infer(x)
    for field in ['unary','factors']:
        for i,row in enumerate(md()[field]):
            for j in range(2 if field=='unary' else 4):
                for val in [True,I(1),1.0,0,10,'1',None]:
                    x=md()
                    if field=='unary':x[field][i][j]=val
                    else:x[field][i][2][j]=val
                    with pytest.raises(ValueError):m.infer(x)


def test_labels_every_slot():
    bad=[S('a'),'','abcdefghi',True,None]+[ch for ch in string.printable if ch not in string.ascii_lowercase]+['é','Ω','中','а','𝚊','a\u200b']
    for val in bad:
        for i in range(3):
            x=bd();x['nodes'][i]=val
            with pytest.raises(ValueError):b.infer(x)
            y=md();y['nodes'][i]=val
            with pytest.raises(ValueError):m.infer(y)
        for i,row in enumerate(bd()['parents']):
            for j in range(len(row)):
                x=bd();x['parents'][i][j]=val
                with pytest.raises(ValueError):b.infer(x)
        # Wrong key types may not be hashable, but all bad fixtures here are.
        x=bd();x['evidence']={val:1}
        with pytest.raises(ValueError):b.infer(x)
        for i in range(2):
            for j in range(2):
                x=md();x['factors'][i][j]=val
                with pytest.raises(ValueError):m.infer(x)
    for ch in [c for c in string.printable if c not in string.ascii_lowercase]+['é','а','中']:
        for label in [ch+'a','a'+ch+'b','a'+ch]:
            x=bd();x['nodes'][2]=label
            with pytest.raises(ValueError):b.infer(x)
            x=md();x['nodes'][2]=label
            with pytest.raises(ValueError):m.infer(x)
    x=bd();x['nodes'][2]='abcdefgh';x['evidence']={};assert b.infer(x)==bo(x)
    x=md();x['nodes'][2]='abcdefgh';x['factors'][1][0]='abcdefgh';assert m.infer(x)==mo(x)


def test_shapes_and_reference_validation():
    for n in [1,7]:
        nodes=list('abcdefg'[:n]);x={'nodes':nodes,'parents':[[] for _ in nodes],'cpt':[[50] for _ in nodes],'evidence':{}}
        with pytest.raises(ValueError):b.infer(x)
        y={'nodes':nodes,'unary':[[1,1] for _ in nodes],'factors':[]}
        with pytest.raises(ValueError):m.infer(y)
    for field,vals in [('nodes',[[],['a','a','c']]),('parents',[[],[[],['a']],[[],['a'],['a','a']],[[],['b'],['a']],[[],['c'],['a']],[[],['a'],['a','b','a']]]),('cpt',[[],[[50]],[[50],[20,80],[10,20]],[[50],[20,80],[1,2,3,4,5]]]),('evidence',[[],{'z':1},{'a':0,'b':1,'c':1,'d':0}])]:
        for val in vals:
            x=bd();x[field]=val
            with pytest.raises(ValueError):b.infer(x)
    for field,vals in [('nodes',[[],['a','a','c']]),('unary',[[],[[1,1]],[[1,1],[1,1],[1]],[[1,1],[1,1],[1,2,3]]]),('factors',[[['a','b',[1,1,1]]],[['a','b',[1,1,1,1,1]]],[['a','b']],[['a','a',[1]*4]],[['a','z',[1]*4]],[['a','b',[1]*4],['b','a',[1]*4]],[['a','b',[1]*4]]*16])]:
        for val in vals:
            x=md();x[field]=val
            with pytest.raises(ValueError):m.infer(x)


def test_contract():
    assert b.ALPHABET==m.ALPHABET=='abcdefghijklmnopqrstuvwxyz'
    assert b.SCOPE=='PARTIAL: exact observational inference in a supplied binary DAG only'
    assert m.SCOPE=='PARTIAL: exact positive-integer binary pairwise MRF inference only'
    assert b.NOT_CLAIMED==('causal identification','intervention inference','parameter learning','production readiness')
    assert m.NOT_CLAIMED==('parameter learning','large-graph inference','causal conclusions','production readiness')


def test_label_boundary_guard_messages():
    for label in ['', 'abcdefghi']:
        x=bd();x['nodes'][2]=label
        with pytest.raises(ValueError,match='^exact lowercase ASCII label required$'):b.infer(x)
        x=md();x['nodes'][2]=label
        with pytest.raises(ValueError,match='^exact lowercase ASCII label required$'):m.infer(x)
    x=md();x['factors']=[['a','b',[1,1,1,1]]]*16
    with pytest.raises(ValueError,match='^factors must be a list of at most 15 records$'):m.infer(x)


def test_evidence_each_position_and_parent_order_guard():
    for evidence in [{'a':0,'b':I(1)},{'a':0,'z':1},{'a':0,S('b'):1},{'a':0,'b':1,'c':True}]:
        x=bd();x['evidence']=evidence
        with pytest.raises(ValueError):b.infer(x)
    for parents in [[[],['b'],['a']],[[],['c'],['a']]]:
        x={'nodes':['a','b','c'],'parents':parents,'cpt':[[50],[25,75],[20,80]],'evidence':{}}
        with pytest.raises(ValueError,match='^parents must precede their child$'):b.infer(x)
