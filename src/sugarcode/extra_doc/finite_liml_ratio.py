"""Row 1063 Limited Information Maximum Likelihood - IV estimation.

Finite-grid least-variance ratio ranking for an intercept/slope equation with
two instruments.4..20 rows[y,x,z1,z2],exact integers-9..9;2..12 distinct
candidate slopes as integer tenths-90..90. Center y,x,z;project residual
u=y-beta*x onto centered instrument span. Score=u'Pz*u/(u'u),equivalent
in ordering to the LIML least-variance ratio u'u/(u'Mz*u). Refuse singular
instrument Gram,zero full residual and zero instrument-residual variance
for any candidate. Return all exact scores,residual sums,first-grid winner.
This is a finite candidate search,NOT the continuous LIML estimator.
NOT_CLAIMED: continuous LIML optimization, instrument validity, statistical
inference, production readiness. Exact containers and caps before scans.
"""
from fractions import Fraction
SCOPE='PARTIAL: finite-grid LIML least-variance ratio ranking only'
NOT_CLAIMED=('continuous LIML optimization','instrument validity','statistical inference','production readiness')


def _pair(value):
    return [value.numerator,value.denominator]


def rank(data):
    if type(data) is not dict or set(data)!={'rows','slopes'}:
        raise ValueError('exact dict with rows and slopes required')
    rows,slopes=data['rows'],data['slopes']
    if type(rows) is not list or not 4<=len(rows)<=20:
        raise ValueError('rows must be an exact list of 4..20 observations')
    if type(slopes) is not list or not 2<=len(slopes)<=12:
        raise ValueError('slopes must be an exact list of 2..12 distinct tenths')
    for value in slopes:
        if type(value) is not int or not -90<=value<=90:
            raise ValueError('slopes must contain exact integer tenths -90..90')
    if len(set(slopes))!=len(slopes):
        raise ValueError('slopes must be unique')
    for row in rows:
        if type(row) is not list or len(row)!=4:
            raise ValueError('row must be an exact list of y,x,z1,z2')
        for value in row:
            if type(value) is not int or not -9<=value<=9:
                raise ValueError('row entries must be exact integers -9..9')
    means=[Fraction(sum(row[i] for row in rows),len(rows)) for i in range(4)]
    centered=[[Fraction(value)-mean for value,mean in zip(row,means)] for row in rows]
    aa=sum(row[2]**2 for row in centered)
    ab=sum(row[2]*row[3] for row in centered)
    bb=sum(row[3]**2 for row in centered)
    determinant=aa*bb-ab**2
    if determinant==0:
        raise ValueError('centered instruments must be linearly independent')
    records=[]
    best=None
    best_score=None
    for tenth in slopes:
        slope=Fraction(tenth,10)
        residual=[row[0]-slope*row[1] for row in centered]
        total=sum(v*v for v in residual)
        if total==0:
            raise ValueError('candidate has zero centered residual variance')
        az=sum(row[2]*u for row,u in zip(centered,residual))
        bz=sum(row[3]*u for row,u in zip(centered,residual))
        projected=(bb*az**2-2*ab*az*bz+aa*bz**2)/determinant
        if total==projected:
            raise ValueError('candidate has zero instrument-residual variance')
        score=projected/total
        records.append({'slope':_pair(slope),'score':_pair(score),'total_ss':_pair(total),'projected_ss':_pair(projected)})
        if best_score is None or score<best_score:
            best=tenth
            best_score=score
    return {'best_tenth':best,'candidates':records,'claims':[False,False,False,False]}
