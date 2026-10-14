from fractions import Fraction as F
import xml.etree.ElementTree as ET
import pytest
from sugarcode.extra_doc.data_visualization import bar_chart as solve


def test_exact_ratio_zero_baseline_and_escaped_label_oracle():
    r=solve(['A&B','<x>','zero'],[3,7,0])
    assert [b['height'] for b in r['bars']]==[F(600,7),200,0]
    assert all(b['y']+b['height']==240 for b in r['bars'])
    assert [b['x'] for b in r['bars']]==[40,120,200] and r['axis_max']==7
    root=ET.fromstring(r['svg']);texts=[e.text for e in root.iter('{http://www.w3.org/2000/svg}text')]
    assert texts==['3','A&B','7','<x>','0','zero']
    assert r['beauty_validated'] is False


def test_all_zero_max_categories_and_integer_boundary():
    assert solve(['x'],[0])['bars'][0]['height']==0
    r=solve(['x'*12]*8,[1000000]*8)
    assert len(r['bars'])==8 and r['axis_max']==1000000
    assert all(b['height']==200 for b in r['bars'])

@pytest.mark.parametrize('args,error,message',[
 ((None,[]),TypeError,'labels and values must be lists or tuples'),
 (([],[]),ValueError,'category count must be between 1 and 8'),
 (([None]*9,[None]*9),ValueError,'category count must be between 1 and 8'),
 ((['x'],[]),ValueError,'label and value counts must match'),
 (([True],[0]),TypeError,'labels must be strings'),
 (([''],[0]),ValueError,'label length must be between 1 and 12'),
 ((['x'*13],[0]),ValueError,'label length must be between 1 and 12'),
 (([' '],[0]),ValueError,'labels must not be blank'),
 ((['x'],[True]),ValueError,'values must be nonbool integers zero through 1000000'),
 ((['x'],[-1]),ValueError,'values must be nonbool integers zero through 1000000'),
 ((['x'],[1000001]),ValueError,'values must be nonbool integers zero through 1000000'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message
