import pytest
from sugarcode.extra_doc.texture_creation import checker_texture as solve


def test_explicit_clipped_checker_pattern_counts_and_no_aliasing():
    a=[255,0,20];b=[0,30,255];r=solve(5,3,a,b,2)
    expected=[[a,a,b,b,a],[a,a,b,b,a],[b,b,a,a,b]]
    assert r['pixels']==expected and r['color_counts']==[8,7]
    assert r['width']==5 and r['height']==3 and r['photorealism_claimed'] is False
    r['pixels'][0][0][0]=1
    assert a[0]==255 and r['pixels'][0][1][0]==255


def test_phase_inversion_one_pixel_max_dimensions_and_defaults():
    import inspect
    assert inspect.signature(solve).parameters['tile_size'].default==8
    assert inspect.signature(solve).parameters['phase'].default==0
    assert solve(1,1,[0,0,0],[255,255,255],128,1)['pixels']==[[[255,255,255]]]
    r=solve(128,128,[0,0,0],[255,255,255],1)
    assert r['color_counts']==[8192,8192]
    a=solve(3,2,[0,0,0],[1,1,1],1,0);b=solve(3,2,[0,0,0],[1,1,1],1,1)
    assert all(sum(x)+sum(y)==3 for ra,rb in zip(a['pixels'],b['pixels']) for x,y in zip(ra,rb))

@pytest.mark.parametrize('args,message',[
 ((True,1,[0]*3,[0]*3),'dimensions must be nonbool integers between 1 and 128'),
 ((0,1,[0]*3,[0]*3),'dimensions must be nonbool integers between 1 and 128'),
 ((1,129,None,None),'dimensions must be nonbool integers between 1 and 128'),
 ((1,1,[0]*3,[0]*3,0),'tile_size must be a nonbool integer between 1 and 128'),
 ((1,1,[0]*3,[0]*3,129),'tile_size must be a nonbool integer between 1 and 128'),
 ((1,1,[0]*3,[0]*3,True),'tile_size must be a nonbool integer between 1 and 128'),
 ((1,1,[0]*3,[0]*3,1,True),'phase must be a nonbool integer zero or one'),
 ((1,1,[0]*3,[0]*3,1,2),'phase must be a nonbool integer zero or one'),
 ((1,1,None,[0]*3),'colors must be RGB lists or tuples'),
 ((1,1,[0]*3,[0]*4),'colors must be RGB lists or tuples'),
 ((1,1,[True,0,0],[0]*3),'channels must be nonbool integers between zero and 255'),
 ((1,1,[0]*3,[-1,0,0]),'channels must be nonbool integers between zero and 255'),
 ((1,1,[0]*3,[256,0,0]),'channels must be nonbool integers between zero and 255'),
])
def test_errors(args,message):
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)==message
