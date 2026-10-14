import xml.etree.ElementTree as ET
import pytest
from sugarcode.extra_doc.generative_art import cellular_art as solve


def test_rule90_xor_oracle_periodic_boundary_and_svg():
    r=solve([0,0,1,0,0],90,4)
    assert r['grid']==[[0,0,1,0,0],[0,1,0,1,0],[1,0,0,0,1],[1,1,0,1,1]]
    assert r['live_cell_count']==9 and r['artistic_quality_validated'] is False
    root=ET.fromstring(r['svg']);assert root.attrib['viewBox']=='0 0 5 4'
    rects=root.find('{http://www.w3.org/2000/svg}g')
    assert {(int(e.attrib['x']),int(e.attrib['y'])) for e in rects}=={(x,y) for y,row in enumerate(r['grid']) for x,v in enumerate(row) if v}


def test_all_neighborhoods_independent_truth_table_and_caps():
    for rule in range(256):
        bits=[int(v) for v in f'{rule:08b}'[::-1]]
        for code in range(8):
            seed=[code//4,(code//2)%2,code%2]
            assert solve(seed,rule,2)['grid'][1][1]==bits[code]
    assert solve([1],255,1)['grid']==[[1]]
    assert len(solve([0]*128,255,128)['grid'])==128

@pytest.mark.parametrize('args,error,message',[
 ((None,0,1),TypeError,'seed must be a list or tuple'),
 (([],0,1),ValueError,'seed width must be between 1 and 128'),
 (([None]*129,0,1),ValueError,'seed width must be between 1 and 128'),
 (([0],True,1),ValueError,'rule must be a nonbool integer zero through 255'),
 (([0],-1,1),ValueError,'rule must be a nonbool integer zero through 255'),
 (([0],256,1),ValueError,'rule must be a nonbool integer zero through 255'),
 (([0],0,True),ValueError,'rows must be a nonbool integer between 1 and 128'),
 (([0],0,0),ValueError,'rows must be a nonbool integer between 1 and 128'),
 (([0],0,129),ValueError,'rows must be a nonbool integer between 1 and 128'),
 (([True],0,1),ValueError,'seed values must be nonbool binary integers'),
 (([2],0,1),ValueError,'seed values must be nonbool binary integers'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message
