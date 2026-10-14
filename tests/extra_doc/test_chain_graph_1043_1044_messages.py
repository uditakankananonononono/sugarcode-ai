"""Auditor-24 regression witnesses: exact guards and messages, rows1043/1044."""
import copy
import pytest
from sugarcode.extra_doc import chain_crf as c
from sugarcode.extra_doc import undirected_separation as g
class L(list):pass
class D(dict):pass

def cd():return {'labels':['a','b'],'unary':[[2,1],[1,3]],'transition':[[2,1],[1,2]]}
def gd():return {'nodes':['a','b','c'],'edges':[['a','b'],['b','c']],'given':[],'source':'a','target':'c'}
def expect(fn,x,message):
    with pytest.raises(ValueError) as exc:fn(x)
    assert str(exc.value)==message

def test_crf_all_messages():
    cases=[({},'exact dict with labels, unary, transition required')]
    for field,value,msg in [
        ('labels',['a'],'labels must be a list of 2..4 labels'),
        ('unary',[],'unary must be a list of 1..6 rows'),
        ('labels',['a','a'],'labels must be unique'),
        ('labels',['a','Bad'],'label must be an exact string of 1..8 lowercase ASCII letters'),
        ('labels',['a',''],'label must be an exact string of 1..8 lowercase ASCII letters'),
        ('transition',[[1,1]],'matrix row count mismatch or non-list'),
        ('transition',[[1,1],[1]],'matrix column count mismatch or non-list'),
        ('unary',[[1,1],[1,0]],'potentials must be exact integers 1..9')]:
        x=cd();x[field]=value;cases.append((x,msg))
    for x,msg in cases:expect(c.infer_chain,x,msg)
    for field,msg in [('labels','labels must be a list of 2..4 labels'),('unary','unary must be a list of 1..6 rows'),('transition','matrix row count mismatch or non-list')]:
        x=cd();x[field]=L(x[field]);expect(c.infer_chain,x,msg)
    for field in ['unary','transition']:
        for i in range(2):
            x=cd();x[field][i]=L(x[field][i]);expect(c.infer_chain,x,'matrix column count mismatch or non-list')
    expect(c.infer_chain,D(cd()),'exact dict with labels, unary, transition required')

def test_separation_all_messages_and_independent_references():
    cases=[({},'exact dict with nodes, edges, given, source, target required')]
    for field,value,msg in [
        ('nodes',['a'],'nodes must be a list of 2..12 identifiers'),
        ('edges',[['a','b']]*31,'edges must be a list of 0..30 pairs'),
        ('given',['b']*13,'given must be a list of 0..12 identifiers'),
        ('nodes',['a','b','Bad'],'label must be an exact string of 1..8 lowercase ASCII letters'),
        ('nodes',['a','b',''],'label must be an exact string of 1..8 lowercase ASCII letters'),
        ('nodes',['a','a','b'],'nodes must be unique'),
        ('given',['z'],'conditioned node is undeclared'),
        ('given',['b','b'],'conditioned nodes must be unique'),
        ('source','z','distinct declared endpoints required'),
        ('target','z','distinct declared endpoints required'),
        ('target','a','distinct declared endpoints required'),
        ('given',['a'],'endpoints must not be conditioned'),
        ('given',['c'],'endpoints must not be conditioned'),
        ('edges',[['a','b'],['b']],'edge must be an exact list pair'),
        ('edges',[['a','b'],['z','b']],'edge must join distinct declared nodes'),
        ('edges',[['a','b'],['b','z']],'edge must join distinct declared nodes'),
        ('edges',[['a','b'],['b','b']],'edge must join distinct declared nodes'),
        ('edges',[['a','b'],['b','a']],'duplicate undirected edge')]:
        x=gd();x[field]=value;cases.append((x,msg))
    # Duplicate nodes must be the only defect: endpoints and edges otherwise valid.
    x=gd();x.update(nodes=['a','a','b'],edges=[['a','b']],target='b');cases.append((x,'nodes must be unique'))
    for x,msg in cases:expect(g.separate,x,msg)
    for field,msg in [('nodes','nodes must be a list of 2..12 identifiers'),('edges','edges must be a list of 0..30 pairs'),('given','given must be a list of 0..12 identifiers')]:
        x=gd();x[field]=L(x[field]);expect(g.separate,x,msg)
    for i in range(2):
        x=gd();x['edges'][i]=L(x['edges'][i]);expect(g.separate,x,'edge must be an exact list pair')
    expect(g.separate,D(gd()),'exact dict with nodes, edges, given, source, target required')
