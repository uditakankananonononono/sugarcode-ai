"""Row 1062 Two-Stage Least Squares - IV estimation.

Intercept/slope2SLS with two supplied instruments.4..20 exact rows[y,x,z1,z2],
integer-9..9. Center variables,solve nonsingular2x2 instrument Gram system
for first-stage x coefficients. Require nonconstant x and nonzero fitted-x
sum of squares. Regress y on fitted x;return slope/intercept,first-stage
coefficients/intercept,fitted x,residuals and first-stage R² as exact fractions.
NOT_CLAIMED: instrument validity, causal identification, standard errors,
production readiness. Exact containers; caps precede scans.
"""
from fractions import Fraction
SCOPE='PARTIAL: centered two-instrument two-stage least squares only'
NOT_CLAIMED=('instrument validity','causal identification','standard errors','production readiness')


def _pair(value):
    return [value.numerator,value.denominator]


def fit(data):
    if type(data) is not dict or set(data)!={'rows'}:
        raise ValueError('exact dict with rows required')
    rows=data['rows']
    if type(rows) is not list or not 4<=len(rows)<=20:
        raise ValueError('rows must be an exact list of 4..20 observations')
    for row in rows:
        if type(row) is not list or len(row)!=4:
            raise ValueError('row must be an exact list of y,x,z1,z2')
        for value in row:
            if type(value) is not int or not -9<=value<=9:
                raise ValueError('entries must be exact integers -9..9')
    n=len(rows)
    ybar,xbar,z1bar,z2bar=[Fraction(sum(row[i] for row in rows),n) for i in range(4)]
    z1=[row[2]-z1bar for row in rows]
    z2=[row[3]-z2bar for row in rows]
    x=[row[1]-xbar for row in rows]
    y=[Fraction(row[0]) for row in rows]
    aa=sum(v*v for v in z1)
    ab=sum(a*b for a,b in zip(z1,z2))
    bb=sum(v*v for v in z2)
    determinant=aa*bb-ab**2
    if determinant==0:
        raise ValueError('centered instruments must be linearly independent')
    xx=sum(v*v for v in x)
    if xx==0:
        raise ValueError('x must vary')
    ax=sum(a*b for a,b in zip(z1,x))
    bx=sum(a*b for a,b in zip(z2,x))
    c1=(bb*ax-ab*bx)/determinant
    c2=(aa*bx-ab*ax)/determinant
    fitted=[c1*a+c2*b for a,b in zip(z1,z2)]
    explained=sum(v*v for v in fitted)
    if explained==0:
        raise ValueError('first-stage fitted x must vary')
    slope=sum(a*b for a,b in zip(fitted,y))/explained
    intercept=ybar-slope*xbar
    first_intercept=xbar-c1*z1bar-c2*z2bar
    return {'slope':_pair(slope),'intercept':_pair(intercept),
            'first_stage_coefficients':[_pair(c1),_pair(c2)],'first_stage_intercept':_pair(first_intercept),
            'fitted_x':[_pair(v+xbar) for v in fitted],
            'residuals':[_pair(row[0]-intercept-slope*row[1]) for row in rows],
            'first_stage_r_squared':_pair(explained/xx),'claims':[False,False,False,False]}
