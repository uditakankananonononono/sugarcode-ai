"""Additive lower-count witnesses for lane1's shipped1736-1759 fixtures."""
import importlib
import pytest

CASES=[
 ('cross_cultural1737','audit',(['q'],[('a',['q']),('b',[])]),([], [('a',['q']),('b',[])]),'requirements must be an exact list with 1..20 entries'),
 ('longitudinal1738','summarize',([('a',0,0)],),([],),'rows must be an exact list with 1..100 entries'),
 ('content1742','count_codes',(['a','b'],[('u',[])]),(['a','b'],[]),'units must be an exact list with 1..100 entries'),
 ('discourse1743','audit_markers',(['a'],['']),([],['']),'markers must be an exact list of 1..20 unique nonwhitespace tokens of 1..80 characters'),
 ('discourse1743','audit_markers',(['a'],['']),(['a'],[]),'texts must be an exact list of 1..100 exact strings of 0..1000 characters'),
 ('narrative1745','audit_events',([('e',0,[])],),([],),'events must be an exact list with 1..100 entries'),
 ('thematic1746','map_themes',([('t',['q'])],[('e',[])]),([],[('e',[])]),'themes must be an exact list with 1..20 entries'),
 ('thematic1746','map_themes',([('t',['q'])],[('e',[])]),([('t',['q'])],[]),'excerpts must be an exact list with 1..100 entries'),
 ('thematic1746','map_themes',([('t',['q'])],[('e',[])]),([('t',[])],[('e',[])]),'themes codes must be an exact list of 1..20 unique valid labels'),
 ('phenomenology1748','summarize',([('a',[])],),([],),'descriptions must be an exact list with 1..100 entries'),
 ('hermeneutics1749','audit_links',(['q1'],[('i1',['q1'])]),([],[('i1',['q1'])]),'passages must be an exact list of 1..100 unique valid labels'),
 ('hermeneutics1749','audit_links',(['q1'],[('i1',['q1'])]),(['q1'],[]),'interpretations must be an exact list with 1..20 entries'),
 ('hermeneutics1749','audit_links',(['q1'],[('i1',['q1'])]),(['q1'],[('i1',[])]),'refs must be an exact list of 1..100 unique known passage labels'),
 ('semiotics1750','audit_signs',([('a',['m'])],),([],),'signs must be an exact list with 1..100 entries'),
 ('semiotics1750','audit_signs',([('a',['m'])],),([('a',[])],),'meanings must be an exact list of 1..20 unique valid labels'),
 ('structural1751','audit_relations',(['a'],[]),([],[]),'nodes must be an exact list of 1..100 unique valid labels'),
 ('critical1753','audit_coverage',(['e'],[('c',[])]),([],[('c',[])]),'evidence must be an exact list of 1..100 unique valid labels'),
 ('critical1753','audit_coverage',(['e'],[('c',[])]),(['e'],[]),'critiques must be an exact list with 1..20 entries'),
 ('queer1755','audit_tags',(['a','b'],[('r',[])]),(['a','b'],[]),'records must be an exact list with 1..100 entries'),
]

@pytest.mark.parametrize('module,fn,one,zero,message',CASES)
def test_count_one_accepted(module,fn,one,zero,message):
    function=getattr(importlib.import_module('sugarcode.extra_doc.'+module),fn)
    assert function(*one)['claim']=='PARTIAL'

@pytest.mark.parametrize('module,fn,one,zero,message',CASES)
def test_count_zero_refused_exactly(module,fn,one,zero,message):
    function=getattr(importlib.import_module('sugarcode.extra_doc.'+module),fn)
    with pytest.raises(ValueError) as exc:function(*zero)
    assert str(exc.value)==message


def test_row1749_single_passage_full_result():
    from sugarcode.extra_doc.hermeneutics1749 import audit_links
    assert audit_links(['q1'],[('i1',['q1'])])=={'links':[('q1',['i1'])],'unreferenced':[],'shared_evidence':[],'claim':'PARTIAL','interpretations_validated':False}
