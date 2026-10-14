from fractions import Fraction as F
from collections import Counter
import pytest
from sugarcode.extra_doc.three_d_modeling import box_mesh as solve


def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))


def test_independent_topology_orientation_and_signed_volume_oracle():
    r=solve([-1,2,F(1,2)],[2,4,F(9,2)])
    vertices=r['vertices'];faces=r['triangles'];center=[F(1,2),3,F(5,2)]
    assert len(vertices)==8 and len(set(tuple(v) for v in vertices))==8 and len(faces)==12
    directed=Counter();volume=F(0)
    for face in faces:
        assert len(face)==3 and len(set(face))==3
        a,b,c=[vertices[i] for i in face]
        normal=cross(sub(b,a),sub(c,a))
        centroid=[(x+y+z)/3 for x,y,z in zip(a,b,c)]
        assert dot(normal,sub(centroid,center))>0
        volume+=dot(a,cross(b,c))/6
        for i,j in zip(face,face[1:]+face[:1]):directed[(i,j)]+=1
    assert all(count==1 and directed[(j,i)]==1 for (i,j),count in directed.items())
    assert len(directed)==36 and len(vertices)-len(directed)//2+len(faces)==2
    assert volume==r['volume']==24 and r['surface_area']==52
    assert r['fabrication_validated'] is False


def test_bounds_match_all_vertices_and_scalar_edges():
    for edge in [2**32-1,F(2**32-1),F(1,2**32-1)]:
        r=solve([0,0,0],[edge,1,1]);assert r['volume']==edge
        assert {v[0] for v in r['vertices']}=={0,edge}
    assert solve([-2,-3,-4],[-1,-1,-1])['volume']==6

@pytest.mark.parametrize('args,error,message',[
 ((None,[1,1,1]),TypeError,'bounds must be lists or tuples'),
 (([0,0,0],None),TypeError,'bounds must be lists or tuples'),
 (([None]*4,[None]*3),ValueError,'bounds must have three coordinates'),
 (([0,0,0],[1,1]),ValueError,'bounds must have three coordinates'),
 (([0,0,0],[1,1,0]),ValueError,'upper coordinates must exceed lower coordinates'),
 (([0,0,0],[1,-1,1]),ValueError,'upper coordinates must exceed lower coordinates'),
 (([True,0,0],[1,1,1]),TypeError,'coordinates must be nonbool int or Fraction'),
 (([0,0,0],[1,1,1.0]),TypeError,'coordinates must be nonbool int or Fraction'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message

@pytest.mark.parametrize('value',[2**32,F(2**32),F(1,2**32)])
def test_next_bit(value):
    with pytest.raises(ValueError,match='^coordinates must fit 32 bits$'):solve([0,0,0],[value,1,1])
