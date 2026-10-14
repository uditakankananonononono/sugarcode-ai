"""Auditor24 omission and exact error-text regression pins1045/1046."""
import pytest
from sugarcode.extra_doc import binary_bayes_net as b
from sugarcode.extra_doc import binary_pairwise_mrf as m
class L(list):pass
class D(dict):pass

def bd():return {'nodes':['a','b'],'parents':[[],['a']],'cpt':[[50],[25,75]],'evidence':{}}
def md():return {'nodes':['a','b'],'unary':[[1,2],[3,1]],'factors':[['a','b',[1,2,3,4]]]}
def expect(fn,x,msg):
    with pytest.raises(ValueError) as err:fn(x)
    assert str(err.value)==msg

def test_bayes_every_message_and_isolated_omissions():
    expect(b.infer,{},'exact dict with nodes, parents, cpt, evidence required')
    cases=[
    ('nodes',['a'],'nodes must be a list of 2..6 labels'),
    ('parents',[],'parents must be one list per node'),
    ('parents',[[],['a'],[]],'parents must be one list per node'),
    ('cpt',[],'cpt must be one list per node'),
    ('cpt',[[50],[25,75],[50]],'cpt must be one list per node'),
    ('evidence',[], 'evidence must be a bounded exact dict'),
    ('evidence',{'a':0,'b':1,'z':0},'evidence must be a bounded exact dict'),
    ('nodes',['a','Bad'],'exact lowercase ASCII label required'),
    ('nodes',['a',''],'exact lowercase ASCII label required'),
    ('parents',[['a'],[]],'parent rows must be exact bounded lists'),
    ('parents',[[],['b']],'parents must precede their child'),
    ('cpt',[[50],[25]],'cpt row size must equal 2**parent_count'),
    ('cpt',[[50],[25,0]],'cpt entries must be exact integer percentages 1..99'),
    ('evidence',{'z':1},'evidence must name declared nodes with exact binary values'),
    ('evidence',{'a':2},'evidence must name declared nodes with exact binary values')]
    for field,val,msg in cases:
        x=bd();x[field]=val;expect(b.infer,x,msg)
    x={'nodes':['a','a'],'parents':[[],[]],'cpt':[[50],[50]],'evidence':{}};expect(b.infer,x,'nodes must be unique')
    x={'nodes':['a','b','c'],'parents':[[],[],['a','a']],'cpt':[[50],[50],[25,50,75,99]],'evidence':{}};expect(b.infer,x,'parents must be unique')
    for field,msg in [('nodes','nodes must be a list of 2..6 labels'),('parents','parents must be one list per node'),('cpt','cpt must be one list per node')]:
        x=bd();x[field]=L(x[field]);expect(b.infer,x,msg)
    for i in range(2):
        x=bd();x['parents'][i]=L(x['parents'][i]);expect(b.infer,x,'parent rows must be exact bounded lists')
        x=bd();x['cpt'][i]=L(x['cpt'][i]);expect(b.infer,x,'cpt row size must equal 2**parent_count')
    x=bd();x['evidence']=D(x['evidence']);expect(b.infer,x,'evidence must be a bounded exact dict')
    expect(b.infer,D(bd()),'exact dict with nodes, parents, cpt, evidence required')

def test_mrf_every_message_and_isolated_omissions():
    expect(m.infer,{},'exact dict with nodes, unary, factors required')
    cases=[
    ('nodes',['a'],'nodes must be a list of 2..6 labels'),
    ('unary',[],'unary must be one list per node'),
    ('unary',[[1,2],[3,1],[1,1]],'unary must be one list per node'),
    ('factors',[['a','b',[1]*4]]*16,'factors must be a list of at most 15 records'),
    ('nodes',['a','Bad'],'exact lowercase ASCII label required'),
    ('nodes',['a',''],'exact lowercase ASCII label required'),
    ('nodes',['a','a'],'nodes must be unique'),
    ('unary',[[1,2],[1]],'potential row must be an exact list with required size'),
    ('unary',[[1,2],[1,0]],'potentials must be exact integers 1..9'),
    ('factors',[['a','b']],'factor record must be an exact three-entry list'),
    ('factors',[['z','b',[1,1,1,1]]],'factor requires distinct declared endpoints'),
    ('factors',[['a','z',[1,1,1,1]]],'factor requires distinct declared endpoints'),
    ('factors',[['a','a',[1,1,1,1]]],'factor requires distinct declared endpoints'),
    ('factors',[['a','b',[1]*4],['b','a',[1]*4]],'duplicate undirected factor')]
    for field,val,msg in cases:
        x=md();x[field]=val;expect(m.infer,x,msg)
    x={'nodes':['a','a'],'unary':[[1,1],[1,1]],'factors':[]};expect(m.infer,x,'nodes must be unique')
    for field,msg in [('nodes','nodes must be a list of 2..6 labels'),('unary','unary must be one list per node'),('factors','factors must be a list of at most 15 records')]:
        x=md();x[field]=L(x[field]);expect(m.infer,x,msg)
    for i in range(2):
        x=md();x['unary'][i]=L(x['unary'][i]);expect(m.infer,x,'potential row must be an exact list with required size')
    x=md();x['factors'][0]=L(x['factors'][0]);expect(m.infer,x,'factor record must be an exact three-entry list')
    x=md();x['factors'][0][2]=L(x['factors'][0][2]);expect(m.infer,x,'potential row must be an exact list with required size')
    expect(m.infer,D(md()),'exact dict with nodes, unary, factors required')
