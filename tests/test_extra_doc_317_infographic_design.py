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
