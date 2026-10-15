"""Row 134 Feature Engineering - Creates informative input variables.

PARTIAL: exact total-degree polynomial feature expansion of supplied integer rows.
Input exact dict rows exact list1..6 of exact list1..4 exact integers-3..3 with
matching width; degree exact int1..3. Include constant monomial. Exponent vectors
ordered by total degree ascending then lexicographically descending (first input
coordinate first). Output exponents integer lists, features integer matrix,
claims3False. No feature selection, predictive usefulness or fitted model claim.
NOT_CLAIMED: informative features, model improvement, production readiness.
"""
from itertools import product
SCOPE='PARTIAL: exact supplied total-degree polynomial feature expansion only'
NOT_CLAIMED=('informative features','model improvement','production readiness')


def expand(data):
    if type(data) is not dict or set(data)!={'rows','degree'}:
        raise ValueError('exact dict with rows and degree required')
    rows,degree=data['rows'],data['degree']
    if type(rows) is not list or not 1<=len(rows)<=6:
        raise ValueError('rows must be an exact list of 1..6 vectors')
    width=None
    for row in rows:
        if type(row) is not list or not 1<=len(row)<=4:
            raise ValueError('vectors must be exact lists of 1..4 values')
        if width is not None and len(row)!=width:
            raise ValueError('vector widths must match')
        width=len(row)
        for v in row:
            if type(v) is not int or not -3<=v<=3:
                raise ValueError('values must be exact integers -3..3')
    if type(degree) is not int or not 1<=degree<=3:
        raise ValueError('degree must be an exact integer 1..3')
    exponents=sorted((e for e in product(range(degree+1),repeat=width) if sum(e)<=degree),key=lambda e:(sum(e),tuple(-v for v in e)))
    features=[]
    for row in rows:
        values=[]
        for exponent in exponents:
            v=1
            for x,power in zip(row,exponent):v*=x**power
            values.append(v)
        features.append(values)
    return {'exponents':list(map(list,exponents)),'features':features,'claims':[False,False,False]}
