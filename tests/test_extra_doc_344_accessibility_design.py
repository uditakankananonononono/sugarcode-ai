import xml.etree.ElementTree as ET
import pytest
from sugarcode.extra_doc.accessibility_design import accessible_page as solve


def test_semantic_heading_skip_link_and_accessible_description_oracle():
    r=solve('A&B',[('First','Text <safe>','A diagram'),('Second','More text',None)])
    root=ET.fromstring(r['html'])
    assert root.attrib['lang']=='en'
    assert root.find('head/title').text=='A&B'
    assert root.find('body/a').attrib['href']=='#main'
    main=root.find('body/main');assert main.attrib=={'id':'main','tabindex':'-1'}
    assert main.find('h1').text=='A&B'
    assert [h.text for h in main.iter('h2')]==['First','Second']
    assert [p.text for p in main.iter('p')]==['Text <safe>','More text']
    svg=next(main.iter('{http://www.w3.org/2000/svg}svg'))
    assert svg.attrib['role']=='img' and svg.attrib['aria-labelledby']=='image-title-0'
    assert svg.find('{http://www.w3.org/2000/svg}title').text=='A diagram'
    assert r['section_count']==2 and r['illustration_count']==1 and r['accessibility_certified'] is False


def test_maximum_shapes_and_absent_illustration():
    r=solve('x'*80,[('h'*80,'p'*1024,'d'*256)]*8)
    assert r['section_count']==8 and r['illustration_count']==8
    assert solve('x',[('h','p',None)])['illustration_count']==0

@pytest.mark.parametrize('args,error,message',[
 (('x',None),TypeError,'sections must be a list or tuple'),
 (('x',[]),ValueError,'section count must be between 1 and 8'),
 (('x',[None]*9),ValueError,'section count must be between 1 and 8'),
 (('x',[None]),ValueError,'sections must contain heading paragraph and optional illustration description'),
 ((True,[('h','p',None)]),TypeError,'text fields must be strings'),
 (('',[('h','p',None)]),ValueError,'text length exceeds supported range'),
 (('x'*81,[('h','p',None)]),ValueError,'text length exceeds supported range'),
 (('x',[('h','p'*1025,None)]),ValueError,'text length exceeds supported range'),
 (('x',[('h','p','d'*257)]),ValueError,'text length exceeds supported range'),
 ((' ',[('h','p',None)]),ValueError,'text fields must not be blank'),
 (('x',[('h','p','')]),ValueError,'text length exceeds supported range'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('text',['a\x00b','a\x01b','a\ufffeb','a\ud800b'])
def test_invalid_xml_chars(text):
    with pytest.raises(ValueError,match='^text must contain only XML-valid characters$'):solve(text,[('h','p',None)])

@pytest.mark.parametrize('field',range(4))
@pytest.mark.parametrize('code',[9,10,13,32,55295,57344,65533,65536,1114111])
def test_xml_char_endpoints_accepted_in_every_field(field,code):
    text='a'+chr(code)+'b';args=['title',[('heading','paragraph','description')]]
    if field==0:args[0]=text
    else:
        section=list(args[1][0]);section[field-1]=text;args[1]=[tuple(section)]
    r=solve(*args)
    assert r['section_count']==1 and r['html'].encode('utf-8')

@pytest.mark.parametrize('field',range(4))
@pytest.mark.parametrize('code',[0,8,11,12,14,31,55296,57343,65534,65535])
def test_xml_gap_endpoints_refused_in_every_field(field,code):
    text='a'+chr(code)+'b';args=['title',[('heading','paragraph','description')]]
    if field==0:args[0]=text
    else:
        section=list(args[1][0]);section[field-1]=text;args[1]=[tuple(section)]
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)=='text must contain only XML-valid characters'


def test_heading_eighty_admitted_eighty_one_refused():
    assert solve('x',[('h'*80,'p',None)])['section_count']==1
    with pytest.raises(ValueError) as exc:solve('x',[('h'*81,'p',None)])
    assert str(exc.value)=='text length exceeds supported range'
