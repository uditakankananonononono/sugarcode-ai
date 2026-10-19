import itertools as it
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import concept504_lens as m


def test_signed_conjugates_and_catalogue():
    values=tuple(x for x in range(-10,11) if x)
    for f in values:
        catalogue=[]
        for u in values:
            denominator=F(1,f)-F(1,u);v=1/denominator if denominator else None
            assert m.image_distance(f,u)==v
            mag=None if v is None else -v/u
            assert m.lateral_magnification(f,u)==mag
            expected=('infinite',None) if v is None else ('positive' if v>0 else 'negative','upright' if mag>0 else 'inverted')
            assert m.image_classification(f,u)==expected
            for h in (-10,0,10):assert m.image_height(f,u,h)==(None if mag is None else h*mag)
            for supplied in values:
                valid=F(1,f)==F(1,u)+F(1,supplied)
                assert m.conjugate_certificate(f,u,supplied)is valid
                if valid:catalogue.append((u,supplied))
        assert m.integer_conjugate_catalogue(f)==tuple(catalogue)


def test_rays_from_homogeneous_line_equations():
    rays=tuple(it.product((-10,-1,0,1,10),repeat=2))
    for f in (-10,-1,1,10):
        for h,s in rays:
            # Line f*y -(f*s-h)*z = f*h, integer-coefficient oracle.
            a=f*s-h
            crossing=('coincident' if h==0 else 'parallel',None) if a==0 else ('unique',F(-f*h,a))
            assert m.axis_crossing(f,(h,s))==crossing
            for z in (-10,-1,0,1,10):
                y=F(f*h+a*z,f);assert m.ray_at_plane(f,(h,s),z)==(y,F(a,f))
                for radius in (0,1,10):assert m.aperture_certificate(f,(h,s),z,radius)is (y*y<=radius*radius)
            for k,t in rays:
                b=f*t-k
                if a==b:expected=('coincident' if h==k else 'parallel',None,None)
                else:
                    z=F(f*(k-h),a-b);y=F(f*h+a*z,f);expected=('unique',z,y)
                assert m.two_ray_intersection(f,(h,s),(k,t))==expected


def refuse(fn,args,code):
    with pytest.raises(ValueError) as exc:fn(*args)
    assert str(exc.value)=='L504:'+code


def test_contract_scope_and_first_bad():
    class I(int):pass
    class T(tuple):pass
    routes=((m.image_distance,(1,)),(m.lateral_magnification,(1,)),(m.image_classification,(1,)),(m.conjugate_certificate,(1,1)),(m.image_height,(1,0)),(m.ray_at_plane,((0,0),0)),(m.axis_crossing,((0,0),)),(m.two_ray_intersection,((0,0),(0,0))),(m.aperture_certificate,((0,0),0,0)),(m.integer_conjugate_catalogue,()))
    for fn,tail in routes:
        for f,code in ((True,'type:f'),(I(1),'type:f'),(-11,'bound:f'),(11,'bound:f'),(0,'zero:f')):refuse(fn,(f,)+tail,code)
    for fn in (m.image_distance,m.lateral_magnification,m.image_classification):
        for u,code in ((True,'type:u'),(I(1),'type:u'),(-11,'bound:u'),(11,'bound:u'),(0,'zero:u')):refuse(fn,(1,u),code)
    for fn,tail in ((m.ray_at_plane,(0,)),(m.axis_crossing,()),(m.two_ray_intersection,((0,0),)),(m.aperture_certificate,(0,0))):
        for ray,code in ((None,'shape:ray'),(T((0,0)),'shape:ray'),((0,),'shape:ray'),((True,0),'type:ray:entry'),((I(0),0),'type:ray:entry'),((-11,0),'bound:ray:entry'),((0,11),'bound:ray:entry')):refuse(fn,(1,ray)+tail,code)
    for v,code in ((True,'type:v'),(0,'zero:v'),(11,'bound:v')):refuse(m.conjugate_certificate,(1,1,v),code)
    for x,code in ((True,'type:'),(-11,'bound:'),(11,'bound:')):
        refuse(m.image_height,(1,1,x),code+'height');refuse(m.ray_at_plane,(1,(0,0),x),code+'z');refuse(m.aperture_certificate,(1,(0,0),0,x),code+'radius')
    refuse(m.aperture_certificate,(1,(0,0),0,-1),'negative:radius')
    refuse(m.two_ray_intersection,(1,(0,0),None),'shape:ray')
    assert m.CLAIMS=={'agi_like_intelligence':False,'physical_optical_validity':False,'production_ready':False}
    assert m.SCOPE=='PARTIAL signed thin-lens algebra and ray fixtures, rational geometry adjacency disclosed'
    assert m.NOT_CLAIMED==('AGI-like intelligence','physical optical validity','optical design','eye or laser safety','production readiness')
