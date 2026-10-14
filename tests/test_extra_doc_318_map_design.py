import xml.etree.ElementTree as ET
import pytest
from sugarcode.extra_doc.map_design import route_map as solve


def test_explicit_route_order_and_xml_geometry_text_oracle():
    r=solve([('A&B',50,400),('<x>',240,80),('end',420,360)],[0,1,2])
    assert r['route_points']==[(50,400),(240,80),(420,360)]
    root=ET.fromstring(r['svg']);line=next(root.iter('{http://www.w3.org/2000/svg}polyline'))
    assert line.attrib['points']=='50,400 240,80 420,360'
    assert [e.text for e in root.iter('{http://www.w3.org/2000/svg}text')]==['A&B','<x>','end']
    assert r['geographic_accuracy_validated'] is False


def test_boundary_counts_single_point_and_route_revisits():
    assert solve([('x'*12,30,440)],[0])['route_points']==[(30,440)]
    r=solve([(str(i),30+i*20,30+i*20) for i in range(16)],[0]*32)
    assert len(r['route_points'])==32
    assert solve([('a',40,40),('b',100,100)],[1,0,1])['route_points']==[(100,100),(40,40),(100,100)]

@pytest.mark.parametrize('args,error,message',[
 ((None,[]),TypeError,'locations and route must be lists or tuples'),
 (([],[0]),ValueError,'location count must be between 1 and 16'),
 (([None]*17,[0]),ValueError,'location count must be between 1 and 16'),
 (([('a',30,30)],[]),ValueError,'route count must be between 1 and 32'),
 (([('a',30,30)],[None]*33),ValueError,'route count must be between 1 and 32'),
 (([None],[0]),ValueError,'locations must contain label x and y'),
 (([(True,30,30)],[0]),TypeError,'labels must be strings'),
 (([('',30,30)],[0]),ValueError,'label length must be between 1 and 12'),
 (([('x'*13,30,30)],[0]),ValueError,'label length must be between 1 and 12'),
 (([(' ',30,30)],[0]),ValueError,'labels must not be blank'),
 (([('a',True,30)],[0]),ValueError,'coordinates must be nonbool integers between 30 and 440'),
 (([('a',29,30)],[0]),ValueError,'coordinates must be nonbool integers between 30 and 440'),
 (([('a',30,441)],[0]),ValueError,'coordinates must be nonbool integers between 30 and 440'),
 (([('a',30,30)],[True]),ValueError,'route indices must be nonbool integers inside location range'),
 (([('a',30,30)],[-1]),ValueError,'route indices must be nonbool integers inside location range'),
 (([('a',30,30)],[1]),ValueError,'route indices must be nonbool integers inside location range'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('label',['a\x00b','a\x01b','a\ufffeb','a\ud800b'])
def test_xml_forbidden_characters(label):
    with pytest.raises(ValueError) as exc:solve([(label,30,30)],[0])
    assert str(exc.value)=='labels must contain only XML-valid characters'


def test_right_edge_label_anchor_inward():
    root=ET.fromstring(solve([('W'*12,440,440)],[0])['svg'])
    text=next(root.iter('{http://www.w3.org/2000/svg}text'))
    assert text.attrib['x']=='432' and text.attrib['text-anchor']=='end'
