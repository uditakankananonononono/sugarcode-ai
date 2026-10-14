"""Row 291 3D Modeling: exact outward-oriented indexed box mesh.

Generates eight rational vertices and twelve oriented triangles for a supplied
axis-aligned box. Faces are watertight, use outward winding, and carry exact
surface area and enclosed volume. No hidden mesh generation service.
NOT_CLAIMED: arbitrary topology, artistic modeling, CAD tolerances, fabrication
readiness, scene rendering or automatic deployment.
"""
from fractions import Fraction


def _number(v):
    if type(v) not in (int,Fraction):raise TypeError('coordinates must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('coordinates must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('coordinates must fit 32 bits')
    return Fraction(v)


def box_mesh(lower,upper):
    if type(lower) not in (list,tuple) or type(upper) not in (list,tuple):
        raise TypeError('bounds must be lists or tuples')
    if len(lower)!=3 or len(upper)!=3:raise ValueError('bounds must have three coordinates')
    lo=[_number(v) for v in lower];hi=[_number(v) for v in upper]
    if any(a>=b for a,b in zip(lo,hi)):raise ValueError('upper coordinates must exceed lower coordinates')
    vertices=[[lo[0],lo[1],lo[2]],[hi[0],lo[1],lo[2]],
              [hi[0],hi[1],lo[2]],[lo[0],hi[1],lo[2]],
              [lo[0],lo[1],hi[2]],[hi[0],lo[1],hi[2]],
              [hi[0],hi[1],hi[2]],[lo[0],hi[1],hi[2]]]
    triangles=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],
               [0,1,5],[0,5,4],[3,7,6],[3,6,2],
               [0,4,7],[0,7,3],[1,2,6],[1,6,5]]
    x,y,z=[b-a for a,b in zip(lo,hi)]
    return {'vertices':vertices,'triangles':triangles,'volume':x*y*z,
            'surface_area':2*(x*y+x*z+y*z),'fabrication_validated':False}
