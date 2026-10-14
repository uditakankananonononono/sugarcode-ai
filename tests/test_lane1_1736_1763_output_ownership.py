"""Mutate every output's mutable containers and keep supplied inputs unchanged.

Immutable exact strings/ints and immutable input tuples may be shared safely.
No mutable input container may be reachable from output, even inside a tuple.
"""
import copy
import importlib
import pytest

CASES=[
 ('comparative1736','compare',([('a',['x','y']),('b',['x'])],)),
 ('cross_cultural1737','audit',(['x','y'],[('a',['x']),('b',['x','y'])])),
 ('longitudinal1738','summarize',([('a',0,2),('a',1,3)],)),
 ('panel1739','audit',([('w1',['a','b']),('w2',['b','c'])],)),
 ('content1742','count_codes',(['x','y'],[('a',['x','y']),('b',[])])),
 ('discourse1743','audit_markers',(['x'],['x x'])),
 ('conversation1744','audit_turns',([('a',1),('b',2)],)),
 ('narrative1745','audit_events',([('a',1,['x']),('b',0,['y'])],)),
 ('thematic1746','map_themes',([('t',['x'])],[('e',['x','y'])])),
 ('grounded1747','track_codes',([('r1',['x']),('r2',['y'])],)),
 ('phenomenology1748','summarize',([('a',['x','y']),('b',['y'])],)),
 ('hermeneutics1749','audit_links',(['x','y'],[('i1',['x']),('i2',['x','y'])])),
 ('semiotics1750','audit_signs',([('a',['x','y']),('b',['x'])],)),
 ('structural1751','audit_relations',(['a','b'],[('a','b'),('b','a')])),
 ('poststructural1752','compare_readings',([('r1',[('t','x')]),('r2',[('t','y')])],)),
 ('critical1753','audit_coverage',(['x','y'],[('a',['x']),('b',[])])),
 ('feminist1754','summarize_resources',([('a',1),('b',2)],)),
 ('queer1755','audit_tags',(['x','y'],[('a',['x','y']),('b',[])])),
 ('race1756','compare_rates',([('a',1,2),('b',2,3)],)),
 ('postcolonial1757','audit_transfers',(['a','b'],[('a','b',1)])),
 ('actor_network1758','audit_network',([('a','human'),('b','nonhuman')],[('a','b')])),
 ('social_network1759','audit_graph',(['a','b','c'],[('a','b'),('b','c'),('a','c')])),
 ('organization1760','audit_structure',([('a',None),('b','a')],)),
 ('institution1761','audit_rules',(['x','y'],[('a',['x']),('b',[])])),
 ('political1762','audit_sectors',([('a',1,2)],)),
 ('public1763','tally',(['x','y'],[('a',['x'])])),
]


def mutable_containers(value):
    if type(value) in (list,dict):yield value
    if type(value) in (list,tuple):
        for child in value:yield from mutable_containers(child)
    elif type(value) is dict:
        for child in value.values():yield from mutable_containers(child)

@pytest.mark.parametrize('module,name,args',CASES)
def test_output_mutation_cannot_change_caller_inputs(module,name,args):
    function=getattr(importlib.import_module('sugarcode.extra_doc.'+module),name)
    before=copy.deepcopy(args);out=function(*args);expected=copy.deepcopy(out)
    inputs={id(c) for c in mutable_containers(args)}
    containers=list(mutable_containers(out))
    assert not inputs.intersection(id(c) for c in containers)
    for c in containers:
        if type(c) is list:c.append('output-only');c.clear()
        else:c['output-only']=True;c.clear()
        assert args==before
    assert function(*args)==expected
