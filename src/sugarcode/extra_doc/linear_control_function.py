"""Row 1064 Control Functions - Handle endogeneity.

Linear residual-inclusion control function with one instrument.4..20 exact
rows[y,x,z],integers-9..9. First regress x on intercept,z;then regress y on
intercept,x,first-stage residual. Require varying instrument,varying fitted
x and nonzero first-stage residual sum of squares. Return first-stage
coefficients/residuals,second-stage intercept,x slope,residual coefficient
and structural residuals,all exact fractions. No causal guarantee inferred.
NOT_CLAIMED: nonlinear control functions, instrument validity, standard
errors, production readiness. Exact containers and caps before scans.
"""
from fractions import Fraction
SCOPE='PARTIAL: exact linear first-stage residual inclusion only'
NOT_CLAIMED=('nonlinear control functions','instrument validity','standard errors','production readiness')


def _pair(value):
    return [value.numerator,value.denominator]


def fit(data):
    if type(data) is not dict or set(data)!={'rows'}:
        raise ValueError('exact dict with rows required')
    rows=data['rows']
    if type(rows) is not list or not 4<=len(rows)<=20:
        raise ValueError('rows must be an exact list of 4..20 observations')
    for row in rows:
        if type(row) is not list or len(row)!=3:
            raise ValueError('row must be an exact list of y,x,z')
        for value in row:
            if type(value) is not int or not -9<=value<=9:
                raise ValueError('entries must be exact integers -9..9')
    n=len(rows)
    ybar,xbar,zbar=[Fraction(sum(row[i] for row in rows),n) for i in range(3)]
    zz=sum((row[2]-zbar)**2 for row in rows)
    if zz==0:
        raise ValueError('instrument must vary')
    zx=sum(row[2]*row[1] for row in rows)-n*zbar*xbar
    first_slope=zx/zz
    if first_slope==0:
        raise ValueError('first-stage fitted x must vary')
    first_intercept=xbar-first_slope*zbar
    residual=[row[1]-first_intercept-first_slope*row[2] for row in rows]
    rr=sum(v*v for v in residual)
    if rr==0:
        raise ValueError('first-stage residual must vary')
    fitted_centered=[first_slope*(row[2]-zbar) for row in rows]
    slope=sum(v*row[0] for v,row in zip(fitted_centered,rows))/sum(v*v for v in fitted_centered)
    residual_total_slope=sum(v*row[0] for v,row in zip(residual,rows))/rr
    control=residual_total_slope-slope
    intercept=ybar-slope*xbar
    structural=[row[0]-intercept-slope*row[1]-control*v for row,v in zip(rows,residual)]
    return {'first_stage_intercept':_pair(first_intercept),'first_stage_slope':_pair(first_slope),
            'first_stage_residuals':[_pair(v) for v in residual],
            'intercept':_pair(intercept),'slope':_pair(slope),'control':_pair(control),
            'residuals':[_pair(v) for v in structural],'claims':[False,False,False,False]}
