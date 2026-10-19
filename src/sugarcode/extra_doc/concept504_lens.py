"""Abstract signed thin-lens and ray fixtures, rational geometry adjacency.

Model 1/f=1/u+1/v, magnification=-v/u. Distances signed exactints
-10..10 excludingzero; conjugates may be rational, None means infinity.
Ray(height,slope) at lensplane transforms slope to slope-height/f,
then propagates by distance z. No real optical design or safety claim.
Ten functions share one application, not ten independent concepts.
"""
from fractions import Fraction as F
SCOPE='PARTIAL signed thin-lens algebra and ray fixtures, rational geometry adjacency disclosed'
NOT_CLAIMED=('AGI-like intelligence','physical optical validity','optical design','eye or laser safety','production readiness')
CLAIMS={'agi_like_intelligence':False,'physical_optical_validity':False,'production_ready':False}


def _fail(c):raise ValueError('L504:'+c)


def _int(x,label,zero=True):
    if type(x)is not int:_fail('type:'+label)
    if not -10<=x<=10:_fail('bound:'+label)
    if not zero and x==0:_fail('zero:'+label)


def _pair(f,u):_int(f,'f',False);_int(u,'u',False)


def _ray(ray):
    if type(ray)is not tuple or len(ray)!=2:_fail('shape:ray')
    for x in ray:_int(x,'ray:entry')


def _image(f,u):return F(f*u,u-f) if u!=f else None


def image_distance(f,u):
    _pair(f,u);return _image(f,u)


def lateral_magnification(f,u):
    _pair(f,u);v=_image(f,u);return None if v is None else -v/u


def image_classification(f,u):
    _pair(f,u);v=_image(f,u)
    if v is None:return ('infinite',None)
    mag=-v/u
    return ('positive' if v>0 else 'negative','upright' if mag>0 else 'inverted')


def conjugate_certificate(f,u,v):
    _pair(f,u);_int(v,'v',False);return u*v==f*(u+v)


def image_height(f,u,height):
    _pair(f,u);_int(height,'height');v=_image(f,u)
    return None if v is None else -v*height/u


def ray_at_plane(f,ray,z):
    _int(f,'f',False);_ray(ray);_int(z,'z');height,slope=ray
    new=F(slope)-F(height,f);return F(height)+z*new,new


def axis_crossing(f,ray):
    """(status,distance): coincident,parallel,orunique."""
    _int(f,'f',False);_ray(ray);h,s=ray;new=F(s)-F(h,f)
    if new==0:return ('coincident' if h==0 else 'parallel',None)
    return 'unique',-h/new


def two_ray_intersection(f,first,second):
    _int(f,'f',False);_ray(first);_ray(second)
    h,s=first;k,t=second;a=F(s)-F(h,f);b=F(t)-F(k,f)
    if a==b:return ('coincident' if h==k else 'parallel',None,None)
    z=F(k-h)/(a-b);return 'unique',z,F(h)+z*a


def aperture_certificate(f,ray,z,radius):
    _int(f,'f',False);_ray(ray);_int(z,'z');_int(radius,'radius')
    if radius<0:_fail('negative:radius')
    h,s=ray;at=F(h)+z*(F(s)-F(h,f));return -radius<=at<=radius


def integer_conjugate_catalogue(f):
    _int(f,'f',False)
    return tuple((u,v) for u in range(-10,11) if u for v in range(-10,11) if v and u*v==f*(u+v))
