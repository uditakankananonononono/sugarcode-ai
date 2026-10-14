"""Row 1061 Instrumental Variables - Handle endogeneity.

Just-identified intercept/slope IV estimate from3..20 exact rows[y,x,z],all
integer-9..9. Center sample sums; require nonconstant instrument and nonzero
centered z-x cross-product. Slope=Cov(z,y)/Cov(z,x),intercept=ybar-slope*xbar.
Return exact coefficients,residuals,first-stage slope and first-stage R². No weak-instrument cutoff. Caps first.
NOT_CLAIMED: instrument validity, causal identification, standard errors,
production readiness. Exact containers only.
"""
from fractions import Fraction
SCOPE='PARTIAL: centered just-identified linear IV with supplied observations only'
NOT_CLAIMED=('instrument validity','causal identification','standard errors','production readiness')


def _pair(value):
    return [value.numerator,value.denominator]


def fit(data):
    if type(data) is not dict or set(data)!={'rows'}:
        raise ValueError('exact dict with rows required')
    rows=data['rows']
    if type(rows) is not list or not 3<=len(rows)<=20:
        raise ValueError('rows must be an exact list of 3..20 observations')
    for row in rows:
        if type(row) is not list or len(row)!=3:
            raise ValueError('row must be an exact list of y,x,z')
        for value in row:
            if type(value) is not int or not -9<=value<=9:
                raise ValueError('entries must be exact integers -9..9')
    n=len(rows)
    ybar,xbar,zbar=[Fraction(sum(row[i] for row in rows),n) for i in range(3)]
    zz=sum((row[2]-zbar)**2 for row in rows)
    zx=sum(row[2]*row[1] for row in rows)-n*zbar*xbar
    zy=sum(row[2]*row[0] for row in rows)-n*zbar*ybar
    if zz==0:
        raise ValueError('instrument must vary')
    if zx==0:
        raise ValueError('centered instrument-times-x product must be nonzero')
    slope=zy/zx
    intercept=ybar-slope*xbar
    residuals=[row[0]-intercept-slope*row[1] for row in rows]
    xx=sum((row[1]-xbar)**2 for row in rows)
    return {'slope':_pair(slope),'intercept':_pair(intercept),'residuals':[_pair(v) for v in residuals],
            'first_stage_slope':_pair(zx/zz),'first_stage_r_squared':_pair(zx**2/(zz*xx)),
            'claims':[False,False,False,False]}
