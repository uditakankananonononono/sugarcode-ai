from fractions import Fraction as F
import xml.etree.ElementTree as ET
import pytest
from sugarcode.extra_doc.infographic_design import fact_infographic as solve


def test_card_geometry_bar_ratio_and_xml_text_oracle():
    r=solve('A&B <facts>',[('first',2),('second',3),('zero',0)])
    assert [c['y'] for c in r['cards']]==[70,160,250]
    assert [c['bar_width'] for c in r['cards']]==[160,240,0]
    assert all(a['y']+a['height']<b['y'] for a,b in zip(r['cards'],r['cards'][1:]))
    text=[e.text for e in ET.fromstring(r['svg']).iter('{http://www.w3.org/2000/svg}text')]
    assert text==['A&B <facts>','first','2','second','3','zero','0']
    assert r['source_facts_verified'] is False


def test_zero_data_caps_and_exact_noninteger_bar():
    assert solve('x',[('x',0)])['cards'][0]['bar_width']==0
    r=solve('x'*40,[('x'*20,1000000)]*6)
    assert len(r['cards'])==6
    assert solve('x',[('a',1),('b',7)])['cards'][0]['bar_width']==F(240,7)

@pytest.mark.parametrize('args,error,message',[
 (('x',None),TypeError,'facts must be a list or tuple'),
 (('x',[]),ValueError,'fact count must be between 1 and 6'),
 (('x',[None]*7),ValueError,'fact count must be between 1 and 6'),
 (('x',[None]),ValueError,'facts must contain label and value'),
 ((True,[('x',0)]),TypeError,'text must be strings'),
 (('',[('x',0)]),ValueError,'text length exceeds supported range'),
 (('x'*41,[('x',0)]),ValueError,'text length exceeds supported range'),
 (('x',[('x'*21,0)]),ValueError,'text length exceeds supported range'),
 ((' ',[('x',0)]),ValueError,'text must not be blank'),
 (('x',[('x',True)]),ValueError,'values must be nonbool integers zero through 1000000'),
 (('x',[('x',-1)]),ValueError,'values must be nonbool integers zero through 1000000'),
 (('x',[('x',1000001)]),ValueError,'values must be nonbool integers zero through 1000000'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('text',['a\x00b','a\x01b','a\ufffeb','a\ud800b'])
@pytest.mark.parametrize('field',[0,1])
def test_xml_forbidden_characters(text,field):
    args=[text,[('x',0)]] if field==0 else ['x',[(text,0)]]
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)=='text must contain only XML-valid characters'


def test_hand_literal_card_and_svg_geometry_contract():
    r=solve('title',[('a',1),('b',2)])
    assert r['cards']==[
        {'x':20,'y':70,'width':360,'height':76,'bar_width':120,'label':'a','value':1},
        {'x':20,'y':160,'width':360,'height':76,'bar_width':240,'label':'b','value':2}]
    root=ET.fromstring(r['svg'])
    assert root.attrib=={'width':'400','height':'260'}
    rects=list(root.iter('{http://www.w3.org/2000/svg}rect'))
    assert [(r.attrib.get('x'),r.attrib.get('y'),r.attrib['width'],r.attrib['height']) for r in rects[1:]]==[
        ('20','70','360','76'),('32','112','120.000000','12'),
        ('20','160','360','76'),('32','202','240.000000','12')]
    texts=list(root.iter('{http://www.w3.org/2000/svg}text'))
    assert [(t.attrib['x'],t.attrib['y'],t.attrib['font-size']) for t in texts]==[
        ('20','38','8'),('32','94','10'),('368','94','10'),('32','184','10'),('368','184','10')]
